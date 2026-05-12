"""Cliente LLM con fallback automatico entre proveedores compatibles con OpenAI."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Iterator, Sequence
from typing import Any

import httpx

from .errors import (
    AllProvidersFailedError,
    AuthError,
    LLMFallbackError,
    ProviderError,
    RateLimitError,
    TransientError,
)
from .providers import DEFAULT_PROVIDERS, ProviderConfig

logger = logging.getLogger("llm_fallback")

Message = dict[str, Any]
MessagesInput = str | Sequence[Message]


def _normalize_messages(
    prompt: MessagesInput,
    *,
    system: str | None = None,
) -> list[Message]:
    """Convierte ``str`` o lista estilo OpenAI en una lista estilo OpenAI."""
    if isinstance(prompt, str):
        msgs: list[Message] = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        return msgs
    msgs = [dict(m) for m in prompt]
    if system and not any(m.get("role") == "system" for m in msgs):
        msgs.insert(0, {"role": "system", "content": system})
    return msgs


class LLM:
    """Cliente con fallback automatico.

    Ejemplo minimo::

        from llm_fallback import LLM
        llm = LLM()
        print(llm.chat("Escribe una funcion que invierta una lista."))

    El cliente intenta cada proveedor en orden. Si recibe 429 (rate limit)
    pone al proveedor en cooldown y prueba el siguiente. Errores 5xx se
    reintentan con backoff antes de cambiar de proveedor.
    """

    def __init__(
        self,
        providers: Sequence[ProviderConfig] = DEFAULT_PROVIDERS,
        *,
        timeout: float = 60.0,
        max_retries_per_provider: int = 2,
        rate_limit_cooldown: float = 60.0,
        load_dotenv: bool = True,
        system_prompt: str | None = None,
    ) -> None:
        if load_dotenv:
            _maybe_load_dotenv()
        self._all_providers: list[ProviderConfig] = list(providers)
        self._timeout = timeout
        self._max_retries = max_retries_per_provider
        self._cooldown = rate_limit_cooldown
        self._cooldown_until: dict[str, float] = {}
        self._disabled: set[str] = set()
        self._system_prompt = system_prompt
        self._client = httpx.Client(timeout=timeout)

    # ------------------------------------------------------------------ API

    def chat(
        self,
        prompt: MessagesInput,
        *,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        model: str | None = None,
        **extra: Any,
    ) -> str:
        """Devuelve la respuesta como ``str``."""
        messages = _normalize_messages(prompt, system=system or self._system_prompt)
        _, payload = self._request_with_provider(
            messages,
            stream=False,
            temperature=temperature,
            max_tokens=max_tokens,
            model_override=model,
            extra=extra,
        )
        return _extract_content(payload)

    def stream(
        self,
        prompt: MessagesInput,
        *,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        model: str | None = None,
        **extra: Any,
    ) -> Iterator[str]:
        """Itera fragmentos de texto a medida que llegan del proveedor."""
        messages = _normalize_messages(prompt, system=system or self._system_prompt)
        yield from self._stream(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            model_override=model,
            extra=extra,
        )

    def raw(
        self,
        prompt: MessagesInput,
        *,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        model: str | None = None,
        **extra: Any,
    ) -> tuple[ProviderConfig, dict[str, Any]]:
        """Devuelve ``(proveedor_usado, respuesta_json)``."""
        messages = _normalize_messages(prompt, system=system or self._system_prompt)
        return self._request_with_provider(
            messages,
            stream=False,
            temperature=temperature,
            max_tokens=max_tokens,
            model_override=model,
            extra=extra,
        )

    # ---------------------------------------------------------------- helpers

    def available_providers(self) -> list[str]:
        """Lista de proveedores listos (con API key y sin cooldown activo)."""
        return [p.name for p in self._candidates()]

    def reset_state(self) -> None:
        """Limpia cooldowns y proveedores deshabilitados (util en tests)."""
        self._cooldown_until.clear()
        self._disabled.clear()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> LLM:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # --------------------------------------------------------------- internas

    def _candidates(self) -> list[ProviderConfig]:
        now = time.monotonic()
        out: list[ProviderConfig] = []
        for p in self._all_providers:
            if p.name in self._disabled:
                continue
            cooldown = self._cooldown_until.get(p.name, 0.0)
            if cooldown > now:
                logger.debug(
                    "Saltando %s (cooldown %.1fs)", p.name, cooldown - now
                )
                continue
            if not p.api_key():
                logger.debug(
                    "Saltando %s (sin API key en $%s)", p.name, p.api_key_env
                )
                continue
            out.append(p)
        return out

    def _request_with_provider(
        self,
        messages: list[Message],
        *,
        stream: bool,
        temperature: float | None,
        max_tokens: int | None,
        model_override: str | None,
        extra: dict[str, Any],
    ) -> tuple[ProviderConfig, dict[str, Any]]:
        candidates = self._candidates()
        if not candidates:
            raise AllProvidersFailedError(
                [
                    (
                        p.name,
                        AuthError(p.name, f"No API key en ${p.api_key_env}"),
                    )
                    for p in self._all_providers
                ]
            )
        attempts: list[tuple[str, Exception]] = []
        for provider in candidates:
            try:
                response = self._call_provider(
                    provider,
                    messages,
                    stream=stream,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model_override=model_override,
                    extra=extra,
                )
                return provider, response
            except RateLimitError as err:
                attempts.append((provider.name, err))
                self._cooldown_until[provider.name] = (
                    time.monotonic() + self._cooldown
                )
                logger.warning(
                    "%s rate-limited, probando siguiente proveedor", provider.name
                )
            except AuthError as err:
                attempts.append((provider.name, err))
                self._disabled.add(provider.name)
                logger.warning(
                    "%s auth invalida, deshabilitado en esta sesion: %s",
                    provider.name,
                    err,
                )
            except (TransientError, ProviderError) as err:
                attempts.append((provider.name, err))
                logger.warning(
                    "%s fallo (%s), probando siguiente proveedor",
                    provider.name,
                    err,
                )
        raise AllProvidersFailedError(attempts)

    def _call_provider(
        self,
        provider: ProviderConfig,
        messages: list[Message],
        *,
        stream: bool,
        temperature: float | None,
        max_tokens: int | None,
        model_override: str | None,
        extra: dict[str, Any],
    ) -> dict[str, Any]:
        url = f"{provider.base_url.rstrip('/')}/chat/completions"
        payload = self._build_payload(
            provider,
            messages,
            stream=stream,
            temperature=temperature,
            max_tokens=max_tokens,
            model_override=model_override,
            extra=extra,
        )
        headers = self._headers(provider)

        for attempt in range(1, self._max_retries + 1):
            try:
                resp = self._client.post(url, json=payload, headers=headers)
            except httpx.RequestError as exc:
                if attempt < self._max_retries:
                    time.sleep(min(2**attempt, 8))
                    continue
                raise TransientError(provider.name, f"red/timeout: {exc}") from exc

            err = _classify(provider.name, resp)
            if err is None:
                return resp.json()
            if isinstance(err, TransientError) and attempt < self._max_retries:
                time.sleep(min(2**attempt, 8))
                continue
            raise err
        raise TransientError(provider.name, "maximo de reintentos alcanzado")

    def _stream(
        self,
        messages: list[Message],
        *,
        temperature: float | None,
        max_tokens: int | None,
        model_override: str | None,
        extra: dict[str, Any],
    ) -> Iterator[str]:
        candidates = self._candidates()
        if not candidates:
            raise AllProvidersFailedError(
                [
                    (
                        p.name,
                        AuthError(p.name, f"No API key en ${p.api_key_env}"),
                    )
                    for p in self._all_providers
                ]
            )
        attempts: list[tuple[str, Exception]] = []
        for provider in candidates:
            try:
                yield from self._stream_provider(
                    provider,
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model_override=model_override,
                    extra=extra,
                )
                return
            except RateLimitError as err:
                attempts.append((provider.name, err))
                self._cooldown_until[provider.name] = (
                    time.monotonic() + self._cooldown
                )
            except AuthError as err:
                attempts.append((provider.name, err))
                self._disabled.add(provider.name)
            except (TransientError, ProviderError) as err:
                attempts.append((provider.name, err))
        raise AllProvidersFailedError(attempts)

    def _stream_provider(
        self,
        provider: ProviderConfig,
        messages: list[Message],
        *,
        temperature: float | None,
        max_tokens: int | None,
        model_override: str | None,
        extra: dict[str, Any],
    ) -> Iterator[str]:
        url = f"{provider.base_url.rstrip('/')}/chat/completions"
        payload = self._build_payload(
            provider,
            messages,
            stream=True,
            temperature=temperature,
            max_tokens=max_tokens,
            model_override=model_override,
            extra=extra,
        )
        headers = self._headers(provider)

        with self._client.stream(
            "POST", url, json=payload, headers=headers
        ) as resp:
            err = _classify_streaming(provider.name, resp)
            if err is not None:
                raise err
            for line in resp.iter_lines():
                if not line:
                    continue
                if line.startswith("data:"):
                    data = line[5:].lstrip()
                else:
                    continue
                if not data:
                    continue
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                token = _extract_delta(chunk)
                if token:
                    yield token

    def _build_payload(
        self,
        provider: ProviderConfig,
        messages: list[Message],
        *,
        stream: bool,
        temperature: float | None,
        max_tokens: int | None,
        model_override: str | None,
        extra: dict[str, Any],
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model_override or provider.model,
            "messages": messages,
            "stream": stream,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        payload.update(extra)
        return payload

    def _headers(self, provider: ProviderConfig) -> dict[str, str]:
        api_key = provider.api_key()
        if not api_key:
            raise AuthError(provider.name, f"No API key en ${provider.api_key_env}")
        scheme = f"{provider.auth_scheme} " if provider.auth_scheme else ""
        headers = {
            "Content-Type": "application/json",
            provider.auth_header: f"{scheme}{api_key}",
        }
        headers.update(provider.extra_headers)
        return headers


# --- Helpers de modulo -----------------------------------------------------


def _classify(provider: str, resp: httpx.Response) -> Exception | None:
    if resp.is_success:
        return None
    text = _truncate(resp.text)
    if resp.status_code == 429:
        return RateLimitError(provider, text, status_code=429)
    if resp.status_code in (401, 403):
        return AuthError(provider, text, status_code=resp.status_code)
    if 500 <= resp.status_code < 600:
        return TransientError(provider, text, status_code=resp.status_code)
    return ProviderError(provider, text, status_code=resp.status_code)


def _classify_streaming(provider: str, resp: httpx.Response) -> Exception | None:
    if resp.is_success:
        return None
    try:
        body = b"".join(resp.iter_bytes()).decode("utf-8", errors="replace")
    except Exception:
        body = "<no body>"
    text = _truncate(body)
    if resp.status_code == 429:
        return RateLimitError(provider, text, status_code=429)
    if resp.status_code in (401, 403):
        return AuthError(provider, text, status_code=resp.status_code)
    if 500 <= resp.status_code < 600:
        return TransientError(provider, text, status_code=resp.status_code)
    return ProviderError(provider, text, status_code=resp.status_code)


def _truncate(text: str, n: int = 400) -> str:
    if len(text) <= n:
        return text
    return text[:n] + "..."


def _extract_content(payload: dict[str, Any]) -> str:
    try:
        choices = payload["choices"]
        if not choices:
            return ""
        msg = choices[0].get("message") or {}
        content = msg.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict)
            )
        return ""
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMFallbackError(
            f"Respuesta inesperada del proveedor: {payload!r}"
        ) from exc


def _extract_delta(chunk: dict[str, Any]) -> str:
    try:
        choices = chunk.get("choices") or []
        if not choices:
            return ""
        delta = choices[0].get("delta") or choices[0].get("message") or {}
        content = delta.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict)
            )
        return ""
    except (AttributeError, TypeError):
        return ""


def _maybe_load_dotenv() -> None:
    """Carga ``.env`` si python-dotenv esta instalado y existe el archivo."""
    try:
        from dotenv import load_dotenv  # type: ignore[import-not-found]
    except ImportError:
        return
    load_dotenv()

"""Excepciones del paquete ``llm_fallback``."""

from __future__ import annotations


class LLMFallbackError(Exception):
    """Base de todas las excepciones del paquete."""


class ProviderError(LLMFallbackError):
    """Error generico devuelto por un proveedor."""

    def __init__(
        self,
        provider: str,
        message: str,
        *,
        status_code: int | None = None,
    ) -> None:
        super().__init__(f"[{provider}] {message}")
        self.provider = provider
        self.status_code = status_code


class RateLimitError(ProviderError):
    """El proveedor devolvio 429 o un equivalente de cuota agotada."""


class AuthError(ProviderError):
    """El proveedor devolvio 401/403 (token invalido o ausente)."""


class TransientError(ProviderError):
    """Error temporal (5xx, timeout, red). El cliente lo reintenta."""


class AllProvidersFailedError(LLMFallbackError):
    """Ningun proveedor pudo atender la peticion."""

    def __init__(self, attempts: list[tuple[str, Exception]]) -> None:
        details = "\n".join(f"  - {name}: {err}" for name, err in attempts)
        super().__init__("Todos los proveedores fallaron:\n" + details)
        self.attempts = attempts

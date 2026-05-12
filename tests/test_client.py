"""Tests del cliente con fallback usando ``pytest-httpx`` para mock HTTP."""

from __future__ import annotations

import json

import httpx
import pytest

from llm_fallback import LLM, ProviderConfig
from llm_fallback.errors import AllProvidersFailedError


def _cfg(name: str, base_url: str, env_var: str) -> ProviderConfig:
    return ProviderConfig(name=name, base_url=base_url, api_key_env=env_var, model="x")


def _make_llm(*configs: ProviderConfig) -> LLM:
    return LLM(providers=configs, load_dotenv=False, rate_limit_cooldown=0.0)


def test_chat_uses_first_provider(monkeypatch, httpx_mock):
    monkeypatch.setenv("KEY_A", "secret-a")
    httpx_mock.add_response(
        url="https://a.example/chat/completions",
        json={"choices": [{"message": {"content": "hola"}}]},
    )
    llm = _make_llm(_cfg("a", "https://a.example", "KEY_A"))
    assert llm.chat("hi") == "hola"


def test_fallback_on_429(monkeypatch, httpx_mock):
    monkeypatch.setenv("KEY_A", "secret-a")
    monkeypatch.setenv("KEY_B", "secret-b")
    httpx_mock.add_response(
        url="https://a.example/chat/completions",
        status_code=429,
        text="rate limited",
    )
    httpx_mock.add_response(
        url="https://b.example/chat/completions",
        json={"choices": [{"message": {"content": "fallback ok"}}]},
    )
    llm = _make_llm(
        _cfg("a", "https://a.example", "KEY_A"),
        _cfg("b", "https://b.example", "KEY_B"),
    )
    assert llm.chat("hi") == "fallback ok"


def test_fallback_on_401(monkeypatch, httpx_mock):
    monkeypatch.setenv("KEY_A", "bad")
    monkeypatch.setenv("KEY_B", "good")
    httpx_mock.add_response(
        url="https://a.example/chat/completions",
        status_code=401,
        text="invalid api key",
    )
    httpx_mock.add_response(
        url="https://b.example/chat/completions",
        json={"choices": [{"message": {"content": "via b"}}]},
    )
    llm = _make_llm(
        _cfg("a", "https://a.example", "KEY_A"),
        _cfg("b", "https://b.example", "KEY_B"),
    )
    assert llm.chat("hi") == "via b"


def test_skips_provider_without_api_key(monkeypatch, httpx_mock):
    monkeypatch.setenv("KEY_B", "secret-b")
    monkeypatch.delenv("KEY_A", raising=False)
    httpx_mock.add_response(
        url="https://b.example/chat/completions",
        json={"choices": [{"message": {"content": "via b"}}]},
    )
    llm = _make_llm(
        _cfg("a", "https://a.example", "KEY_A"),
        _cfg("b", "https://b.example", "KEY_B"),
    )
    assert llm.chat("hi") == "via b"


def test_all_fail_raises(monkeypatch, httpx_mock):
    monkeypatch.setenv("KEY_A", "secret-a")
    httpx_mock.add_response(
        url="https://a.example/chat/completions",
        status_code=429,
        text="rate limited",
        is_reusable=True,
    )
    llm = LLM(
        providers=[_cfg("a", "https://a.example", "KEY_A")],
        load_dotenv=False,
        max_retries_per_provider=1,
        rate_limit_cooldown=0.0,
    )
    with pytest.raises(AllProvidersFailedError) as ei:
        llm.chat("hi")
    assert "a:" in str(ei.value)


def test_no_keys_at_all_raises(monkeypatch):
    monkeypatch.delenv("KEY_A", raising=False)
    monkeypatch.delenv("KEY_B", raising=False)
    llm = _make_llm(
        _cfg("a", "https://a.example", "KEY_A"),
        _cfg("b", "https://b.example", "KEY_B"),
    )
    with pytest.raises(AllProvidersFailedError):
        llm.chat("hi")


def test_system_prompt_inserted(monkeypatch, httpx_mock):
    monkeypatch.setenv("KEY_A", "secret-a")
    captured: dict = {}

    def _capture(request):
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "ok"}}]}
        )

    httpx_mock.add_callback(_capture, url="https://a.example/chat/completions")
    llm = LLM(
        providers=[_cfg("a", "https://a.example", "KEY_A")],
        load_dotenv=False,
        system_prompt="Eres un experto",
    )
    llm.chat("hola")
    msgs = captured["payload"]["messages"]
    assert msgs[0] == {"role": "system", "content": "Eres un experto"}
    assert msgs[1] == {"role": "user", "content": "hola"}


def test_messages_list_passthrough(monkeypatch, httpx_mock):
    monkeypatch.setenv("KEY_A", "secret-a")
    captured: dict = {}

    def _capture(request):
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "ok"}}]}
        )

    httpx_mock.add_callback(_capture, url="https://a.example/chat/completions")
    llm = _make_llm(_cfg("a", "https://a.example", "KEY_A"))
    llm.chat(
        [
            {"role": "system", "content": "S"},
            {"role": "user", "content": "U"},
        ]
    )
    msgs = captured["payload"]["messages"]
    assert msgs == [
        {"role": "system", "content": "S"},
        {"role": "user", "content": "U"},
    ]


def test_streaming(monkeypatch, httpx_mock):
    monkeypatch.setenv("KEY_A", "secret-a")
    body = (
        b'data: {"choices":[{"delta":{"content":"Ho"}}]}\n\n'
        b'data: {"choices":[{"delta":{"content":"la"}}]}\n\n'
        b"data: [DONE]\n\n"
    )
    httpx_mock.add_response(
        url="https://a.example/chat/completions",
        content=body,
        headers={"content-type": "text/event-stream"},
    )
    llm = _make_llm(_cfg("a", "https://a.example", "KEY_A"))
    assert "".join(llm.stream("hi")) == "Hola"


def test_streaming_fallback(monkeypatch, httpx_mock):
    monkeypatch.setenv("KEY_A", "secret-a")
    monkeypatch.setenv("KEY_B", "secret-b")
    httpx_mock.add_response(
        url="https://a.example/chat/completions",
        status_code=429,
        text="rate limited",
    )
    body = (
        b'data: {"choices":[{"delta":{"content":"hey"}}]}\n\n'
        b"data: [DONE]\n\n"
    )
    httpx_mock.add_response(
        url="https://b.example/chat/completions",
        content=body,
        headers={"content-type": "text/event-stream"},
    )
    llm = _make_llm(
        _cfg("a", "https://a.example", "KEY_A"),
        _cfg("b", "https://b.example", "KEY_B"),
    )
    assert "".join(llm.stream("hi")) == "hey"


def test_raw_returns_provider_and_payload(monkeypatch, httpx_mock):
    monkeypatch.setenv("KEY_A", "secret-a")
    httpx_mock.add_response(
        url="https://a.example/chat/completions",
        json={"choices": [{"message": {"content": "ok"}}], "id": "abc"},
    )
    llm = _make_llm(_cfg("a", "https://a.example", "KEY_A"))
    provider, payload = llm.raw("hi")
    assert provider.name == "a"
    assert payload["id"] == "abc"


def test_available_providers(monkeypatch):
    monkeypatch.setenv("KEY_A", "secret-a")
    monkeypatch.delenv("KEY_B", raising=False)
    llm = _make_llm(
        _cfg("a", "https://a.example", "KEY_A"),
        _cfg("b", "https://b.example", "KEY_B"),
    )
    assert llm.available_providers() == ["a"]


def test_authorization_header(monkeypatch, httpx_mock):
    monkeypatch.setenv("KEY_A", "my-token")
    captured: dict = {}

    def _capture(request):
        captured["auth"] = request.headers.get("Authorization")
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "ok"}}]}
        )

    httpx_mock.add_callback(_capture, url="https://a.example/chat/completions")
    llm = _make_llm(_cfg("a", "https://a.example", "KEY_A"))
    llm.chat("hi")
    assert captured["auth"] == "Bearer my-token"

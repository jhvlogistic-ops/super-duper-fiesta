"""Configuracion de proveedores LLM compatibles con la API de OpenAI."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class ProviderConfig:
    """Describe un endpoint compatible con la API de OpenAI.

    Los tres proveedores soportados por defecto (Claude via GitHub Models,
    Gemini 2.5 Pro via Google AI Studio y DeepSeek) exponen el mismo formato
    de ``/chat/completions``, por lo que solo cambian ``base_url``, ``model``
    y la variable de entorno donde vive el API key.
    """

    name: str
    """Identificador legible (usado en logs y mensajes de error)."""

    base_url: str
    """URL base sin ``/chat/completions`` (se anade automaticamente)."""

    api_key_env: str
    """Nombre de la variable de entorno que contiene el API key."""

    model: str
    """Identificador del modelo a usar con este proveedor."""

    extra_headers: Mapping[str, str] = field(default_factory=dict)
    """Cabeceras HTTP adicionales (por ejemplo ``Api-Version``)."""

    auth_scheme: str = "Bearer"
    """Esquema de autorizacion. Usar ``""`` para enviar la clave sin prefijo."""

    auth_header: str = "Authorization"
    """Nombre de la cabecera de autenticacion."""

    def api_key(self) -> str | None:
        """Devuelve el API key resuelto desde el entorno (o ``None``)."""
        return os.environ.get(self.api_key_env)


# --- Proveedores por defecto -----------------------------------------------

# Orden de preferencia: Claude (mejor para edicion de codigo) -> Gemini Pro
# (mejor para contexto largo) -> DeepSeek (mas barato).

CLAUDE_SONNET_45 = ProviderConfig(
    name="github-models-claude",
    base_url="https://models.github.ai/inference",
    api_key_env="GITHUB_MODELS_TOKEN",
    model="anthropic/claude-sonnet-4.5",
)

GEMINI_PRO = ProviderConfig(
    name="gemini-2.5-pro",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai",
    api_key_env="GOOGLE_API_KEY",
    model="gemini-2.5-pro",
)

DEEPSEEK_CHAT = ProviderConfig(
    name="deepseek",
    base_url="https://api.deepseek.com",
    api_key_env="DEEPSEEK_API_KEY",
    model="deepseek-chat",
)

DEFAULT_PROVIDERS: tuple[ProviderConfig, ...] = (
    CLAUDE_SONNET_45,
    GEMINI_PRO,
    DEEPSEEK_CHAT,
)


# --- Proveedores alternativos preconfigurados -------------------------------

GITHUB_GPT5 = ProviderConfig(
    name="github-models-gpt5",
    base_url="https://models.github.ai/inference",
    api_key_env="GITHUB_MODELS_TOKEN",
    model="openai/gpt-5",
)

GEMINI_FLASH = ProviderConfig(
    name="gemini-2.5-flash",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai",
    api_key_env="GOOGLE_API_KEY",
    model="gemini-2.5-flash",
)

DEEPSEEK_REASONER = ProviderConfig(
    name="deepseek-reasoner",
    base_url="https://api.deepseek.com",
    api_key_env="DEEPSEEK_API_KEY",
    model="deepseek-reasoner",
)

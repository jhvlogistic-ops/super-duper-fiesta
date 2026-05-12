"""llm_fallback: cliente LLM con fallback automatico entre proveedores gratuitos.

Uso rapido::

    from llm_fallback import LLM
    llm = LLM()
    print(llm.chat("Escribe una funcion Python que invierta una lista."))

Variables de entorno (al menos UNA es necesaria):

* ``GITHUB_MODELS_TOKEN`` - Claude Sonnet 4.5 via GitHub Models
* ``GOOGLE_API_KEY``      - Gemini 2.5 Pro via Google AI Studio
* ``DEEPSEEK_API_KEY``    - DeepSeek V3.1

Ver ``README.md`` para detalles de configuracion y ejemplos.
"""

from .client import LLM, Message, MessagesInput
from .errors import (
    AllProvidersFailedError,
    AuthError,
    LLMFallbackError,
    ProviderError,
    RateLimitError,
    TransientError,
)
from .providers import (
    DEFAULT_PROVIDERS,
    GEMINI_FLASH,
    GITHUB_GPT5,
    ProviderConfig,
)

__version__ = "0.1.0"

__all__ = [
    "LLM",
    "Message",
    "MessagesInput",
    "ProviderConfig",
    "DEFAULT_PROVIDERS",
    "GEMINI_FLASH",
    "GITHUB_GPT5",
    "LLMFallbackError",
    "ProviderError",
    "RateLimitError",
    "AuthError",
    "TransientError",
    "AllProvidersFailedError",
    "__version__",
]

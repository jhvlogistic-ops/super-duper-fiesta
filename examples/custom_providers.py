"""Ejemplo de configuracion personalizada de proveedores y modelos."""

from llm_fallback import GEMINI_FLASH, GITHUB_GPT5, LLM, ProviderConfig
from llm_fallback.providers import CLAUDE_SONNET_45


def main() -> None:
    # Orden personalizado: primero Gemini Flash (rapido), luego Claude.
    llm = LLM(providers=[GEMINI_FLASH, CLAUDE_SONNET_45, GITHUB_GPT5])
    print(llm.chat("Da un consejo corto para escribir codigo Python limpio."))

    # Tambien puedes anadir un proveedor propio (cualquier endpoint
    # compatible con la API de OpenAI, como Groq, OpenRouter, etc.).
    groq = ProviderConfig(
        name="groq-qwen3-coder",
        base_url="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY",
        model="qwen/qwen3-coder-30b",
    )
    custom = LLM(providers=[groq, CLAUDE_SONNET_45])
    print(custom.chat("dame una funcion fibonacci iterativa"))


if __name__ == "__main__":
    main()

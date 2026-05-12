"""Ejemplo minimo: chat sin streaming."""

from llm_fallback import LLM


def main() -> None:
    llm = LLM(system_prompt="Eres un asistente de programacion Python conciso.")
    respuesta = llm.chat(
        "Escribe una funcion que invierta una lista sin usar slicing [::-1]."
    )
    print(respuesta)


if __name__ == "__main__":
    main()

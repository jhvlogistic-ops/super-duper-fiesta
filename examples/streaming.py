"""Ejemplo de streaming: imprime el texto a medida que llega."""

from llm_fallback import LLM


def main() -> None:
    llm = LLM()
    for chunk in llm.stream(
        "Explica brevemente que es un decorador en Python con un ejemplo."
    ):
        print(chunk, end="", flush=True)
    print()


if __name__ == "__main__":
    main()

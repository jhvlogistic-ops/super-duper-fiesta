"""REPL minimo para usar el cliente como asistente de codigo.

Uso:

    python examples/coding_assistant.py

Pega tu codigo y termina con una linea que contenga solo ``###``.
Ctrl+C para salir.
"""

from __future__ import annotations

from llm_fallback import LLM

SYSTEM = (
    "Eres un experto en Python. Recibes codigo incompleto o con bugs y "
    "devuelves una version corregida y comentada brevemente. Responde "
    "siempre con un bloque de codigo entre triple backticks seguido de "
    "una explicacion corta."
)


def main() -> None:
    llm = LLM(system_prompt=SYSTEM)
    print("Pega codigo y termina con '###'. Ctrl+C para salir.")
    while True:
        try:
            buffer: list[str] = []
            while True:
                line = input()
                if line.strip() == "###":
                    break
                buffer.append(line)
            if not buffer:
                continue
            for chunk in llm.stream("\n".join(buffer)):
                print(chunk, end="", flush=True)
            print("\n---")
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            return


if __name__ == "__main__":
    main()

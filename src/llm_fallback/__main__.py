"""CLI: ``python -m llm_fallback "tu prompt"`` o ``llm-fallback "tu prompt"``."""

from __future__ import annotations

import argparse
import sys

from .client import LLM
from .errors import AllProvidersFailedError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="llm-fallback",
        description=(
            "Pregunta a Claude (via GitHub Models) con fallback a Gemini "
            "2.5 Pro y DeepSeek. Necesita al menos una de las variables "
            "GITHUB_MODELS_TOKEN, GOOGLE_API_KEY o DEEPSEEK_API_KEY."
        ),
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Texto del prompt. Si se omite, se lee de stdin.",
    )
    parser.add_argument("--system", help="Mensaje de sistema opcional.")
    parser.add_argument("--model", help="Forzar un modelo para todos los providers.")
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Deshabilitar streaming y mostrar todo de golpe.",
    )
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument(
        "--list-providers",
        action="store_true",
        help="Listar los proveedores disponibles y salir.",
    )
    args = parser.parse_args(argv)

    llm = LLM()

    if args.list_providers:
        for name in llm.available_providers():
            print(name)
        return 0

    prompt = args.prompt if args.prompt is not None else sys.stdin.read()
    if not prompt or not prompt.strip():
        parser.error("prompt vacio")
        return 2

    try:
        if args.no_stream:
            text = llm.chat(
                prompt,
                system=args.system,
                model=args.model,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
            )
            print(text)
        else:
            for chunk in llm.stream(
                prompt,
                system=args.system,
                model=args.model,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
            ):
                print(chunk, end="", flush=True)
            print()
    except AllProvidersFailedError as exc:
        print(f"\n[error] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

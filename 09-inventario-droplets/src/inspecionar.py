import argparse
import json

from langchain_anthropic.chat_models import convert_to_anthropic_tool

from src.ferramentas import docstring, modelo_pydantic

FORMAS = {
    "1": ("docstring", docstring.listar_droplets),
    "2": ("Pydantic", modelo_pydantic.listar_droplets),
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mostra o que o modelo recebe de cada forma da ferramenta."
    )
    parser.add_argument("forma", nargs="?", choices=FORMAS, help="Sem forma, mostra as duas.")
    args = parser.parse_args()

    for numero in [args.forma] if args.forma else FORMAS:
        nome, ferramenta = FORMAS[numero]
        enviado = convert_to_anthropic_tool(ferramenta)

        print(f"\n===== {numero}. {nome} =====")
        print(f"name: {enviado['name']}")
        print(f"description: {enviado['description']}")
        print("input_schema:")
        print(json.dumps(enviado["input_schema"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

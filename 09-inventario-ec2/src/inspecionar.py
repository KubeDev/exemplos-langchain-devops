import argparse
import json

from langchain_anthropic.chat_models import convert_to_anthropic_tool

from src.ferramentas import anotada, docstring, docstring_sem_parse, modelo_pydantic

FORMAS = {
    "1": ("docstring sem parse", docstring_sem_parse.listar_instancias),
    "2": ("docstring com parse", docstring.listar_instancias),
    "3": ("Annotated", anotada.listar_instancias),
    "4": ("Pydantic", modelo_pydantic.listar_instancias),
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mostra o que o modelo recebe de cada forma da ferramenta."
    )
    parser.add_argument("forma", nargs="?", choices=FORMAS, help="Sem forma, mostra todas.")
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

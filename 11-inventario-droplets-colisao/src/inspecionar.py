import argparse
import json

from langchain_anthropic.chat_models import convert_to_anthropic_tool

from src.ferramentas import ambiguas, contrastivas

VERSOES = {
    "ambiguas": [ambiguas.listar_droplets, ambiguas.verificar_saude],
    "contrastivas": [contrastivas.listar_droplets, contrastivas.verificar_saude],
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mostra o que o modelo recebe de cada versão do inventário."
    )
    parser.add_argument("versao", nargs="?", choices=VERSOES, help="Sem versão, mostra as duas.")
    args = parser.parse_args()

    for versao in [args.versao] if args.versao else VERSOES:
        print(f"\n===== {versao} =====")
        for ferramenta in VERSOES[versao]:
            enviado = convert_to_anthropic_tool(ferramenta)

            print(f"\nname: {enviado['name']}")
            print(f"description: {enviado['description']}")
            print("input_schema:")
            print(json.dumps(enviado["input_schema"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

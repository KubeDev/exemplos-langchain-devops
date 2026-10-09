from dotenv import load_dotenv

# O pytest carrega o conftest.py antes de qualquer teste: é o lugar de preparar o ambiente.
# O pytest não lê o .env: sem isto, DIGITALOCEAN_TOKEN não chega à ferramenta.
load_dotenv()

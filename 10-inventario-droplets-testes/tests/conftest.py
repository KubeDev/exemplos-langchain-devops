from dotenv import load_dotenv

# O pytest não lê o .env: sem isto, DIGITALOCEAN_TOKEN não chega à ferramenta.
load_dotenv()

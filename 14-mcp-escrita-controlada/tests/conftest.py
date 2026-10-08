from dotenv import load_dotenv

# O pytest não lê o .env: sem isto, DIGITALOCEAN_TOKEN não chega ao teste do Droplet.
load_dotenv()

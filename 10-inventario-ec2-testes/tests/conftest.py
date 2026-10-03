from dotenv import load_dotenv

# O pytest não lê o .env: sem isto, AWS_PROFILE e AWS_REGION não chegam ao boto3.
load_dotenv()

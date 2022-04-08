from dotenv import load_dotenv
load_dotenv('local.env')

from os import getenv
ENV_NAME = getenv('ENV_NAME')
LOG_LEVEL = getenv('LOG_LEVEL').upper()
MAX_THREADS = int(getenv('MAX_THREADS'))
API_HOST = getenv('API_HOST')
API_PORT = getenv('API_PORT')
AWS_ACCESS_KEY_ID = getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = getenv('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_REGION = getenv('AWS_DEFAULT_REGION')
TWILIO_ACCOUNT_SID = getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = getenv('TWILIO_PHONE_NUMBER')
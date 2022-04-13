from dotenv import load_dotenv
load_dotenv('local.env')

from os import getenv
PORT = int(getenv('PORT'))
ENV_NAME = getenv('ENV_NAME')
LOG_LEVEL = getenv('LOG_LEVEL').upper()
MAX_THREADS = int(getenv('MAX_THREADS'))
DATABASE_URL = getenv('DATABASE_URL')
TWILIO_ACCOUNT_SID = getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = getenv('TWILIO_PHONE_NUMBER')
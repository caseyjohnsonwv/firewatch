from dotenv import load_dotenv
load_dotenv()

from os import getenv
ENV_NAME = getenv('ENV_NAME')
API_HOST = getenv('HOST')
API_PORT = getenv('PORT')
THREAD_COUNT = int(getenv('THREAD_COUNT'))
TWILIO_ACCOUNT_SID = getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = getenv('TWILIO_PHONE_NUMBER')
from dotenv import load_dotenv
load_dotenv('local.env')

from os import getenv
ENV_NAME = getenv('ENV_NAME')
LOG_LEVEL = getenv('LOG_LEVEL').upper()
MAX_THREADS = int(getenv('MAX_THREADS'))
DATABASE_URL = getenv('DATABASE_URL')
HEROKU_APP_NAME = getenv('HEROKU_APP_NAME') # set by heroku env
TWILIO_ACCOUNT_SID = getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = getenv('TWILIO_PHONE_NUMBER')
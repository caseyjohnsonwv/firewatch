from dotenv import load_dotenv
load_dotenv()

from os import getenv
API_HOST = getenv('HOST')
API_PORT = getenv('PORT')
IBM_API_KEY = getenv('IBM_API_KEY')
IBM_API_URL = getenv('IBM_API_URL')
ENV_NAME = getenv('ENV_NAME')
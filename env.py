from dotenv import load_dotenv
load_dotenv()

from os import getenv
API_HOST = getenv('HOST') or "localhost"
API_PORT = getenv('PORT') or "5000"
IBM_API_KEY = getenv('IBM_API_KEY')
IBM_API_URL = getenv('IBM_API_URL')
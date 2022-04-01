from dotenv import load_dotenv
load_dotenv()

from os import getenv
API_HOST = getenv('HOST') or "localhost"
API_PORT = getenv('PORT') or "5000"
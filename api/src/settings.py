from starlette.config import Config

config = Config(".env")

DEBUG = config("DEBUG", cast=bool, default=False)
HOST = config("HOST", default="localhost")
PORT = config("PORT", cast=int, default=8000)
API_URL = config("API_URL", default="https://api.openmeasures.io/content")
DATABASE_URL = config("DATABASE_URL")

from starlette.config import Config

config = Config(".env")

DEBUG = config("DEBUG", cast=bool, default=False)
HOST = config("HOST", default="0.0.0.0")
PORT = config("PORT", cast=int, default=8000)
DATABASE_URL = config("DATABASE_URL")

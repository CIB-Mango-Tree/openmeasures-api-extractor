from os import path
from starlette.config import Config
from .utils.user_dir import get_app_data_dir


config = Config(path.join(get_app_data_dir(), ".env"))
DEBUG = config("DEBUG", cast=bool, default=False)
HOST = config("HOST", default="localhost")
PORT = config("PORT", cast=int, default=8000)
API_URL = config("API_URL", default="https://api.openmeasures.io/content")
DATABASE_URL = config("DATABASE_URL", default=f"sqlite:///{get_app_data_dir()}/app.db")

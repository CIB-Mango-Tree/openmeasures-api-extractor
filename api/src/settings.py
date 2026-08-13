from os import path
from pathlib import Path
import sys
from starlette.config import Config
from .utils.user_dir import get_app_data_dir


def _spa_dir() -> Path:
    """Location of the built frontend, which this server also serves.

    Bundled as `dist` inside the PyInstaller archive; resolved relative to the repo when running
    from source.
    """
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")) / "dist"

    # api/src/settings.py -> site/dist
    return Path(__file__).resolve().parents[2] / "site" / "dist"


config = Config(path.join(get_app_data_dir(), ".env"))
DEBUG = config("DEBUG", cast=bool, default=False)
HOST = config("HOST", default="127.0.0.1")
PORT = config("PORT", cast=int, default=8000)
API_URL = config("API_URL", default="https://api.openmeasures.io/content")
DATABASE_URL = config("DATABASE_URL", default=f"sqlite:///{get_app_data_dir()}/app.db")
SPA_DIR = Path(config("SPA_DIR", default=str(_spa_dir())))

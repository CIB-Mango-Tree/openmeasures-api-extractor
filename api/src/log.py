from logging import (
    getLogger,
    basicConfig,
    StreamHandler,
    Formatter,
    FileHandler,
    DEBUG,
    INFO,
    ERROR,
)
from sys import stdout
from os import path
from .settings import DEBUG as APP_DEBUG
from .utils.user_dir import get_app_data_dir

root_logger = getLogger()
sqlalchemy_logger = getLogger("sqlalchemy.engine")
sqlalchemy_pool_logger = getLogger("sqlalchemy.pool")
stream_handler = StreamHandler(stdout)
formatter = Formatter("%(asctime)s | %(name)s [%(levelname)s]:    %(message)s")

root_logger.setLevel(DEBUG if APP_DEBUG else ERROR)
root_logger.handlers.clear()
stream_handler.setFormatter(formatter)
root_logger.addHandler(stream_handler)
sqlalchemy_logger.setLevel(DEBUG if APP_DEBUG else ERROR)
sqlalchemy_pool_logger.setLevel(DEBUG if APP_DEBUG else ERROR)

if not APP_DEBUG:
    file_handler = FileHandler(
        path.join(get_app_data_dir(), "app.log"), mode="w", encoding="utf-8"
    )

    file_handler.setLevel(ERROR)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
    uvicorn_logger = getLogger(logger_name)
    uvicorn_logger.handlers.clear()
    uvicorn_logger.propagate = True
    uvicorn_logger.setLevel(DEBUG if APP_DEBUG else ERROR)

logger = getLogger(__name__)

# Always-on diagnostics logger: writes to a file regardless of DEBUG so packaged-app
# users (who are never in DEBUG) can capture and send back request/WS connection details.
diagnostics_logger = getLogger("diagnostics")
diagnostics_logger.setLevel(INFO)
diagnostics_logger.propagate = False
_diagnostics_handler = FileHandler(
    path.join(get_app_data_dir(), "diagnostics.log"), mode="a", encoding="utf-8"
)
_diagnostics_handler.setLevel(INFO)
_diagnostics_handler.setFormatter(formatter)
diagnostics_logger.addHandler(_diagnostics_handler)

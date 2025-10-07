from starlette.responses import JSONResponse
from pydantic import BaseModel
from typing import Any


def error_response(code: int, data: dict[str, Any] | list[Any]) -> JSONResponse:
    return JSONResponse({"code": code, "error": data}, status_code=code)

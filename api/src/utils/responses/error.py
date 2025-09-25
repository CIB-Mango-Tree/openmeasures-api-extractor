from starlette.responses import JSONResponse
from typing import Dict, Any


def error_response(code: int, data: Dict[str, Any]) -> JSONResponse:
    return JSONResponse({"code": code, "error": data})

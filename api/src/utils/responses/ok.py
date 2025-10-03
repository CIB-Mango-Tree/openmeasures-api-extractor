from starlette.responses import JSONResponse
from typing import Any


def OK_response(code: int, data: Any) -> JSONResponse:
    return JSONResponse({"code": code.value, "data": data}, status_code=code)


def OK_collection_response(code: int, data: list[Any]) -> JSONResponse:
    return JSONResponse(
        {"code": code, "count": len(data), "data": data}, status_code=code
    )

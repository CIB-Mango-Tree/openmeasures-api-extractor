from starlette.responses import JSONResponse
from enum import Enum
from typing import Any


class OKCodes(Enum):
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    RESET_CONTENT = 205
    PARTIAL_CONTENT = 206


def OK_response(code: OKCodes, data: Any) -> JSONResponse:
    return JSONResponse({"code": code.value, "data": data}, status_code=code.value)


def OK_collection_response(code: OKCodes, data: list[Any]) -> JSONResponse:
    return JSONResponse(
        {"code": code.value, "count": len(data), "data": data}, status_code=code.value
    )

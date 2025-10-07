from starlette.responses import JSONResponse
from pydantic import BaseModel
from typing import Any


def OK_response(code: int, data: Any) -> JSONResponse:
    if isinstance(data, BaseModel):
        return JSONResponse(
            {"code": code, "data": data.model_dump(mode="json")}, status_code=code
        )

    return JSONResponse({"code": code, "data": data}, status_code=code)


def OK_collection_response(code: int, data: list[Any]) -> JSONResponse:
    data_length = len(data)

    if all(isinstance(item, BaseModel) for item in data):
        return JSONResponse(
            {
                "code": code,
                "count": data_length,
                "data": [item.model_dump(mode="json") for item in data],
            },
            status_code=code,
        )

    return JSONResponse(
        {"code": code, "count": data_length, "data": data}, status_code=code
    )

from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse
from ..utils.responses import OK_collection_response
from ..utils.constants import PLATFORMS
from typing import cast


class PlatformsEndpoint(HTTPEndpoint):
    def get(self, request: Request) -> JSONResponse:
        output: list[dict[str, str]] = []

        for key, value in PLATFORMS.items():
            readable = cast(str, value.get("readable", ""))
            output.append({"value": key, "readable": readable})

        return OK_collection_response(200, output)

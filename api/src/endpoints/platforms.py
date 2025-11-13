from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse
from ..utils.responses import OK_collection_response
from ..utils.constants import PLATFORMS
from typing import cast


class PlatformsEndpoint(HTTPEndpoint):
    def get(self, _: Request) -> JSONResponse:
        return OK_collection_response(
            200,
            [
                {"value": key, "readable": cast(str, value.get("readable", ""))}
                for key, value in PLATFORMS.items()
            ],
        )

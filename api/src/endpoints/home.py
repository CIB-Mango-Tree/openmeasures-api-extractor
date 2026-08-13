from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.endpoints import HTTPEndpoint


class Home(HTTPEndpoint):
    async def get(self, _: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})

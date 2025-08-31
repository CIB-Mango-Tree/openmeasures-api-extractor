from starlette.responses import JSONResponse
from starlette.endpoints import HTTPEndpoint


class Home(HTTPEndpoint):
    async def get(self, request):
        return JSONResponse({"hello": "world!"})

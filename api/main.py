from starlette.applications import Starlette
from src.endpoints import endpoints
import uvicorn

app = Starlette(debug=True, routes=endpoints)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

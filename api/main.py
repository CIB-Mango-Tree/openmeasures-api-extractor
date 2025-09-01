from starlette.applications import Starlette
from src.endpoints import endpoints
import uvicorn


def main() -> None:
    app = Starlette(debug=True, routes=endpoints)
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()

from starlette.routing import Route
from .home import Home

endpoints = [Route("/", Home)]
__all__ = ["endpoints"]

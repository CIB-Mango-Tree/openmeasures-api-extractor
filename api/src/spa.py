from pathlib import Path
from starlette.exceptions import HTTPException
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope
from .log import logger


class SPAStaticFiles(StaticFiles):
    """Serves the built frontend, falling back to index.html for unknown paths.

    Plain StaticFiles(html=True) resolves directories to index.html but still 404s on a path that
    does not exist on disk. Client-side routes are exactly that, so without the fallback a reload
    on any route other than "/" would fail.
    """

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            return await super().get_response(path, scope)

        except HTTPException as error:
            if error.status_code != 404:
                raise

            # Let genuinely missing assets 404 rather than handing back HTML, which would turn a
            # broken script tag into a confusing parse error in the browser.
            if "." in Path(path).name:
                raise

            return await super().get_response("index.html", scope)


def mount_path(directory: Path) -> Path | None:
    if not directory.is_dir():
        logger.warning(
            "frontend build not found at %s; the API will run but no UI will be served", directory
        )
        return None

    if not (directory / "index.html").is_file():
        logger.warning("frontend build at %s has no index.html", directory)
        return None

    return directory

from pathlib import Path
from typing import Any
import webview
from .log import logger
from .services import QueryExportService
from .validator import ExportParamValidator


class DesktopApi:
    """Bridge exposed to the page as `window.pywebview.api`.

    Downloads are the reason this exists. A `Content-Disposition: attachment` response makes a
    browser save the file, but the webview has no download manager -- it just navigates, so the
    export rendered inside the window instead of being saved. Going through here produces a real
    native save dialog and writes the file where the user chooses.
    """

    def __init__(self, export_service: QueryExportService) -> None:
        self._export_service = export_service
        self._window: webview.Window | None = None

    def bind(self, window: "webview.Window") -> None:
        self._window = window

    def save_export(self, query_id: str, export_format: str) -> dict[str, Any]:
        try:
            params = ExportParamValidator.model_validate(
                {"id": query_id, "format": export_format}
            )
            file_export = self._export_service.export(params)

        except Exception:
            logger.error("export failed for query %s", query_id, exc_info=True)
            return {"status": "error", "message": "The export could not be generated."}

        if file_export is None:
            return {"status": "error", "message": "That query has no data to export."}

        if self._window is None:
            return {"status": "error", "message": "No window is available to save from."}

        target = self._window.create_file_dialog(
            webview.SAVE_DIALOG, save_filename=file_export.filename
        )

        # The dialog returns None (or an empty selection) when the user cancels.
        if not target:
            return {"status": "cancelled"}

        destination = Path(target[0] if isinstance(target, (list, tuple)) else target)

        try:
            destination.write_bytes(file_export.data)

        except OSError:
            logger.error("could not write export to %s", destination, exc_info=True)
            return {"status": "error", "message": f"Could not write to {destination}."}

        logger.info("export written to %s", destination)

        return {"status": "saved", "path": str(destination)}

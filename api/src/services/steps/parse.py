import polars as pl
from sqlalchemy.orm import selectinload
from ...db.models import Query
from ...log import logger
from ...storage import clean_frame, drop_empty_columns, read_raw, write_processed
from ...utils.constants import (
    CLEAN_CONTINUE,
    CLEAN_IN_PROGRESS,
    PARSE_CONTINUE,
    PARSE_IN_PROGRESS,
    PARSE_INCOMPLETE,
)
from .base import Outcome, ProcessingStep, StepResult


class ParseStep(ProcessingStep):
    """Turns the raw Parquet pages into the processed dataset.

    Sanitization happens here rather than in a stage of its own. It used to write a near-complete
    duplicate of every hit into requests.cleaned_data; it is now a read-time transform between raw
    and processed, which is what removed the third copy of every post. Keeping it as a separate
    stage would mean either reintroducing that intermediate artifact or rewriting the raw pages in
    place -- and clean_text is not idempotent ("&amp;amp;" -> "&amp;" -> "&"), so re-running an
    in-place clean would corrupt the data.
    """

    continue_status = PARSE_CONTINUE
    in_progress_status = PARSE_IN_PROGRESS
    incomplete_status = PARSE_INCOMPLETE

    def handles(self, status: str) -> bool:
        # CLEAN:* no longer has a stage, but a query persisted mid-flight by an older build can
        # still be sitting in one, and the frontend can still ask to resume at CLEAN:CONTINUE.
        return super().handles(status) or status in (CLEAN_CONTINUE, CLEAN_IN_PROGRESS)

    def execute(self, query: Query) -> StepResult | None:
        # Reloaded for its requests: fetch created the request rows, and the raw pages are named
        # after them.
        reloaded = self._query_repo.find_by_id(
            query.id, [selectinload(Query.requests), selectinload(Query.terms)]
        )

        if reloaded is None:
            return None

        # The raw pages already carry the columns declared for the platform, so there is no
        # schema inference here -- just read, clean, drop unused columns, write.
        request_ids = [request.id for request in reloaded.requests]
        frame: pl.DataFrame | None = read_raw(reloaded.id, request_ids)

        if frame is None:
            raise ValueError(f"no raw dataset found for query {reloaded.id}")

        logger.debug("read %d raw rows for query %s", frame.height, reloaded.id)

        write_processed(
            reloaded.id, drop_empty_columns(clean_frame(reloaded.platform, frame))
        )

        # Last step in the pipeline, so the orchestrator resolves ADVANCE to COMPLETE.
        return StepResult(
            query=reloaded, outcome=Outcome.ADVANCE, message="query is now complete"
        )

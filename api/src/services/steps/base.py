from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import ClassVar
from pydantic import BaseModel, ConfigDict
from pyventus.events import EventEmitter
from ...db.models import Query
from ...db.repositories import QueryRepository
from ...event import Event
from ...log import logger
from ...serializers import QuerySerializer


class Outcome(Enum):
    """What a step concluded, from which the orchestrator derives the next status."""

    # Work is done; hand the query to the next step in the pipeline.
    ADVANCE = auto()
    # There is nothing further to do for this query at all -- skip the remaining steps.
    COMPLETE = auto()
    # Stopped short and can be resumed later (quota exhausted, or awaiting user approval).
    PAUSE = auto()


class StepResult(BaseModel):
    """A step's report to the orchestrator.

    Steps no longer decide their own successor's status. They describe what happened and the
    orchestrator maps that onto a status transition, so the pipeline order is expressed in one
    place instead of being hardcoded across the steps.
    """

    # Query is a SQLAlchemy model, not a pydantic type, so it has to be allowed through as-is.
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    query: Query
    outcome: Outcome
    message: str | None = None


class ProcessingStep(ABC):
    """One stage of the extraction pipeline.

    Each stage previously repeated the same preamble: promote CONTINUE to IN_PROGRESS, bail out
    on INCOMPLETE, and wrap the body in a try/except that logged and returned None. That is now
    here, and subclasses implement only execute().

    Steps run on a worker thread (asyncio.to_thread) and emit progress from there, crossing back
    into the event loop inside WebSocketService. That has to stay: moving emission into the
    orchestrator's async context would change the delivery semantics the frontend relies on.
    """

    continue_status: ClassVar[str]
    in_progress_status: ClassVar[str]
    incomplete_status: ClassVar[str]

    def __init__(self, query_repo: QueryRepository, emitter: EventEmitter) -> None:
        self._query_repo = query_repo
        self._emitter = emitter

    def handles(self, status: str) -> bool:
        return status in (self.continue_status, self.in_progress_status)

    def run(self, query: Query) -> StepResult | None:
        if query.status == self.continue_status:
            query = self._resume(query)

        if query.status == self.incomplete_status:
            return None

        try:
            return self.execute(query)

        except Exception as error:
            logger.error(
                "%s failed for query %s", type(self).__name__, query.id, exc_info=error
            )
            return None

    def _resume(self, query: Query) -> Query:
        query.status = self.in_progress_status

        query.set_updated_at()

        # skip_relationships: only the status changed, and a full merge would cascade into the
        # query's terms and requests for no benefit.
        query = self._query_repo.update(query, True)

        self.on_resume(query)

        return query

    def on_resume(self, query: Query) -> None:
        """Called when a paused query is resumed. Override to emit a progress event."""

    def emit(self, event: str, query: Query, message: str | None = None) -> None:
        self._emitter.emit(
            event,
            payload=Event(
                data=QuerySerializer.convert_model_to_dict(query), message=message
            ),
        )

    @abstractmethod
    def execute(self, query: Query) -> StepResult | None:
        """Performs the stage.

        Returns what happened; the orchestrator persists the resulting status and emits it.
        Returning None aborts the pipeline for this query.
        """

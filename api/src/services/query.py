from sqlalchemy.orm import selectinload
from pyventus.events import EventEmitter, EventLinker
from asyncio import Task, create_task, to_thread
from uuid import UUID
from typing import Sequence
from ..db.models import Query, QueryTerm
from ..db.repositories import QueryRepository, QueryTermRepository
from ..validator import (
    CreateQueryValidator,
    UpdateQueryValidator,
    DeleteQueriesValidator,
    TermValidator,
    ParamValidator,
)
from ..event import Event
from ..serializers import QuerySerializer
from ..utils.constants import (
    QUERY_COMPLETE,
    FETCH_INCOMPLETE,
    FETCH_CONTINUE,
    CLEAN_CONTINUE,
    PARSE_CONTINUE,
    PARSE_INCOMPLETE,
)
from ..storage import delete_dataset
from .steps import Outcome, ProcessingStep, StepResult
from ..log import logger


class QueryService:
    _query_repo: QueryRepository
    _query_term_repo: QueryTermRepository
    _emitter: EventEmitter
    _steps: Sequence[ProcessingStep]

    def __init__(
        self,
        query_repo: QueryRepository,
        query_term_repo: QueryTermRepository,
        emitter: EventEmitter,
        steps: Sequence[ProcessingStep],
    ) -> None:
        self._emitter = emitter
        self._query_repo = query_repo
        self._query_term_repo = query_term_repo
        # Injected rather than constructed here: the pipeline is composed in main.py, so the
        # service depends only on the ProcessingStep interface. Order matters -- each step
        # advances the status into the next one's range.
        self._steps = steps

    def _next_status(
        self, step: ProcessingStep, outcome: Outcome, remaining: Sequence[ProcessingStep]
    ) -> str:
        """Maps a step's outcome onto the status to persist and emit.

        ADVANCE resolves against the pipeline order rather than anything the step names, so the
        sequence of stages is expressed in one place. A step that advances with nothing after it
        has finished the query.
        """
        if outcome is Outcome.PAUSE:
            return step.incomplete_status

        if outcome is Outcome.COMPLETE or not remaining:
            return QUERY_COMPLETE

        return remaining[0].in_progress_status

    def _apply(
        self, step: ProcessingStep, result: StepResult, remaining: Sequence[ProcessingStep]
    ) -> Query:
        query = result.query
        status = self._next_status(step, result.outcome, remaining)

        query.status = status

        query.set_updated_at()

        query = self._query_repo.update(query, True)

        # The event name is the status: that is the WebSocket protocol the frontend switches on.
        self._emitter.emit(
            status,
            payload=Event(
                data=QuerySerializer.convert_model_to_dict(query), message=result.message
            ),
        )

        return query

    def process_query(self, id: UUID) -> Task[None]:
        async def func() -> None:
            query = self._query_repo.find_by_id(
                id, [selectinload(Query.terms), selectinload(Query.requests)]
            )

            if query is None:
                return

            for index, step in enumerate(self._steps):
                if not step.handles(query.status):
                    continue

                logger.debug(
                    "%s starting for query %s (status: %s)",
                    type(step).__name__,
                    query.id,
                    query.status,
                )

                # Steps are blocking (HTTP, SQLAlchemy, Parquet), so each runs on a worker
                # thread. The transition runs there too: it writes to the database, and emitting
                # from the loop thread would block it.
                result = await to_thread(step.run, query)

                if result is None:
                    return

                remaining = self._steps[index + 1 :]
                query = await to_thread(self._apply, step, result, remaining)

                # PAUSE and COMPLETE both end the pipeline for this query.
                if result.outcome is not Outcome.ADVANCE:
                    return

            logger.debug(
                "query %s finished - PLATFORM: %s STATUS: %s PROGRESS: %s ROWS FETCHED: %d",
                query.id,
                query.platform,
                query.status,
                query.percentage,
                query.rows_fetched,
            )

        task = create_task(func())
        cancel_event = f"CANCEL:{str(id)}"

        @EventLinker.once(cancel_event)
        def handle_task_cancel() -> None:
            if task.done():
                return

            logger.debug("Cancelling processing task for query: %s", str(id))
            task.cancel()

        # EventLinker is a process-global registry and `once` only unregisters when it fires. A
        # query that completes normally would otherwise leave its handler behind forever, one per
        # query, for the lifetime of the application.
        def discard_cancel_handler(_: Task[None]) -> None:
            EventLinker.remove(cancel_event, handle_task_cancel)

        task.add_done_callback(discard_cancel_handler)

        # Returned so callers (and tests) can await completion; the endpoints ignore it and let
        # processing continue in the background.
        return task

    def get(self, include_requests: bool = False) -> list[Query]:
        if include_requests:
            return self._query_repo.find_all(
                [selectinload(Query.terms), selectinload(Query.requests)]
            )

        return self._query_repo.find_all()

    def get_by_id(self, id: UUID, incldue_requests: bool = False) -> Query | None:
        if incldue_requests:
            return self._query_repo.find_by_id(
                id, [selectinload(Query.terms), selectinload(Query.requests)]
            )

        return self._query_repo.find_by_id(id)

    def get_by_status(self, status: str, include_requests: bool = False) -> list[Query]:
        if include_requests:
            return self._query_repo.find_by_status(
                status, [selectinload(Query.terms), selectinload(Query.requests)]
            )

        return self._query_repo.find_by_status(status)

    def get_by_platform(
        self, platform: str, incldue_requests: bool = False
    ) -> list[Query]:
        if incldue_requests:
            return self._query_repo.find_by_platform(
                platform, [selectinload(Query.terms), selectinload(Query.requests)]
            )

        return self._query_repo.find_by_platform(platform)

    def create(self, data: CreateQueryValidator) -> Query:
        logger.debug(
            "validated data for potential new query - platform: %s start_date: %s end_date: %s terms: %s",
            data.platform,
            data.start_date,
            data.end_date,
            data.terms,
        )
        query = Query(
            start_date=data.start_date, end_date=data.end_date, platform=data.platform
        )

        if data.timezone is not None:
            query.timezone = data.timezone

        query = self._query_repo.create(query)

        terms: list[QueryTerm] = []

        for index in range(len(data.terms)):
            item: TermValidator = data.terms[index]

            terms.append(
                QueryTerm(
                    query_id=query.id,
                    term=item.term,
                    modifier=item.modifier.value,
                    position=index + 1,
                )
            )

        self._query_term_repo.batch_create(terms)

        query = self._query_repo.find_by_id(
            query.id, [selectinload(Query.terms), selectinload(Query.requests)]
        )

        if query is None:
            raise ValueError("query service shit itself during refresh...")

        self.process_query(query.id)

        return query

    def update(self, id: UUID, data: UpdateQueryValidator) -> Query | None:
        query = self._query_repo.find_by_id(id)

        if query is None:
            return None

        if query.status == FETCH_INCOMPLETE and data.status == FETCH_CONTINUE:
            query.status = FETCH_CONTINUE

        # CLEAN:CONTINUE is still accepted from the frontend but normalized onto the parse stage:
        # cleaning is a transform inside ParseStep, not a stage of its own. The former
        # CLEAN:INCOMPLETE branch is gone -- nothing ever assigned that status.
        if query.status == FETCH_INCOMPLETE and data.status == CLEAN_CONTINUE:
            query.status = PARSE_CONTINUE

        if query.status == PARSE_INCOMPLETE and data.status == PARSE_CONTINUE:
            query.status = PARSE_CONTINUE

        self._emitter.emit(f"CANCEL:{str(query.id)}")

        query = self._query_repo.update(query)

        self.process_query(query.id)

        return query

    def delete(self, data: ParamValidator) -> None:
        if not self._query_repo.exists(data.id):
            return

        self._emitter.emit(f"CANCEL:{str(data.id)}")
        self._query_repo.delete(data.id)
        # Post data lives on disk now, so deleting the row is no longer enough to reclaim it.
        delete_dataset(data.id)

    def batch_delete(self, data: DeleteQueriesValidator) -> None:
        ids: list[UUID] = []

        for id in data.ids:
            if not self._query_repo.exists(id):
                continue

            self._emitter.emit(f"CANCEL:{str(id)}")
            ids.append(id)

        self._query_repo.batch_delete(ids)

        for id in ids:
            delete_dataset(id)

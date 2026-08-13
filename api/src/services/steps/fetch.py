from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo
from pyventus.events import EventEmitter
from sqlalchemy.orm import selectinload
from ...db.models import Query, QueryRequest
from ...db.repositories import QueryRepository, QueryRequestRepository
from ...log import logger
from ...storage import extract_hits, write_raw_page
from ...utils.constants import (
    FETCH_CONTINUE,
    FETCH_INCOMPLETE,
    FETCH_IN_PROGRESS,
    FETCH_UPDATE_PROGRESS,
    PLATFORMS,
)
from ..openmeasures import OpenMeasuresClient, RateLimited
from .base import Outcome, ProcessingStep, StepResult
from .quota import QuotaTracker

PAGE_SIZE = 10000
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"


class FetchStep(ProcessingStep):
    """Pages the OpenMeasures API, writing each page to Parquet.

    Reports an outcome rather than choosing the next status: the orchestrator owns transitions.
    Progress events emitted mid-loop (FETCH:UPDATE_PROGRESS) are not transitions and stay here.
    """

    continue_status = FETCH_CONTINUE
    in_progress_status = FETCH_IN_PROGRESS
    incomplete_status = FETCH_INCOMPLETE

    def __init__(
        self,
        query_repo: QueryRepository,
        emitter: EventEmitter,
        request_repo: QueryRequestRepository,
        quota: QuotaTracker,
        client: OpenMeasuresClient,
    ) -> None:
        super().__init__(query_repo, emitter)

        self._request_repo = request_repo
        self._quota = quota
        self._client = client

    def on_resume(self, query: Query) -> None:
        logger.debug(
            "continued query has been updated - id: %s status: %s", query.id, query.status
        )
        self.emit(FETCH_UPDATE_PROGRESS, query)

    def _initial_params(self, query: Query) -> tuple[dict[str, Any], float, datetime]:
        start = query.start_date.replace(tzinfo=ZoneInfo(query.timezone))
        end = query.end_date.replace(tzinfo=ZoneInfo(query.timezone))
        since = (
            query.current_timestamp.replace(tzinfo=ZoneInfo(query.timezone))
            if query.current_timestamp is not None
            else start
        )
        params: dict[str, Any] = {
            "site": query.platform,
            "term": query.term,
            "since": since.strftime(TIMESTAMP_FORMAT),
            "until": end.strftime(TIMESTAMP_FORMAT),
            "limit": PAGE_SIZE,
            "querytype": "boolean_content",
        }

        return params, (end - start).total_seconds() / 3600, start

    def _persist(self, query: Query) -> Query:
        """Saves the fields this step accumulated. The status transition is the orchestrator's."""
        query.set_updated_at()

        return self._query_repo.update(query, True)

    def execute(self, query: Query) -> StepResult | None:
        limit = self._quota.load()

        if limit is None:
            return None

        params, query_range, start = self._initial_params(query)

        logger.debug("request params: %s", params)

        outcome = Outcome.ADVANCE
        message = "data fetch is now complete"

        while True:
            limit = self._quota.refresh_if_due(limit)

            if self._quota.is_exhausted(limit):
                self._quota.announce_exhausted(limit)

                outcome = Outcome.PAUSE
                message = "data fetch is imcomplete. query has been paused due to limit being exhausted"
                break

            try:
                payload = self._client.fetch(params)

            except RateLimited:
                limit = self._quota.exhaust(limit)

                self._quota.announce_exhausted(limit)

                outcome = Outcome.PAUSE
                message = "data fetch is imcomplete. query has been paused due to limit being exhausted"
                break

            hits: list[dict[str, Any]] = payload.get("hits", {}).get("hits", [])

            if not hits and query.current_timestamp is None:
                # Nothing matched at all: there is no data to parse, so the pipeline is done.
                query.percentage = 1.0

                outcome = Outcome.COMPLETE
                message = "query is now complete"
                break

            hit_length = len(hits)
            request = self._request_repo.create(
                QueryRequest(row_count=hit_length, query_id=query.id)
            )

            # The row is created first so the page file can be named after its id, keeping the
            # request row and its Parquet page 1:1 without a path column.
            write_raw_page(query.id, request.id, extract_hits(query.platform, hits))

            limit = self._quota.consume(limit)

            query.rows_fetched += hit_length

            query.increment_queries_used()

            if hit_length < PAGE_SIZE:
                query.percentage = 1.0
                break

            timestamp_column = PLATFORMS.get(query.platform, {}).get(
                "created_at_column", None
            )

            if timestamp_column is None:
                raise ValueError(f"unknown platform during fetch: {query.platform}")

            last_created_at = hits[-1]["_source"].get(timestamp_column)

            if not last_created_at:
                query.percentage = 1.0
                break

            last_created_at_datetime = datetime.fromisoformat(last_created_at)
            fetched_hours = (
                last_created_at_datetime.replace(tzinfo=ZoneInfo(query.timezone)) - start
            ).total_seconds() / 3600

            query.percentage = fetched_hours / query_range
            query.current_timestamp = last_created_at_datetime

            if hit_length == PAGE_SIZE and query.rows_fetched == PAGE_SIZE:
                outcome = Outcome.PAUSE
                message = "data fetch is imcomplete. user must approve finishing the query to continue"
                break

            params["since"] = last_created_at

            query = self._persist(query)

            self.emit(FETCH_UPDATE_PROGRESS, query)

        self._persist(query)

        reloaded = self._query_repo.find_by_id(
            query.id, [selectinload(Query.terms), selectinload(Query.requests)]
        )

        if reloaded is None:
            return None

        return StepResult(query=reloaded, outcome=outcome, message=message)

from pandas import DataFrame
from requests import get
from pyventus.events import EventEmitter, EventLinker
from asyncio import create_task, to_thread
from uuid import UUID
from datetime import datetime
from zoneinfo import ZoneInfo
from ..db.models import Query, QueryTerm, QueryRequest
from ..db.repositories import (
    QueryRepository,
    QueryTermRepository,
    QueryRequestRepository,
    QueryLimitRepository,
)
from ..validator import (
    CreateQueryValidator,
    UpdateQueryValidator,
    DeleteQueriesValidator,
    ParamValidator,
)
from ..serializers import QuerySerializer
from ..event import Event
from ..utils.sanitize import clean_text
from ..utils.constants import (
    FETCH_INCOMPLETE,
    FETCH_CONTINUE,
    FETCH_IN_PROGRESS,
    FETCH_UPDATE_PROGRESS,
    CLEAN_IN_PROGRESS,
    CLEAN_CONTINUE,
    CLEAN_INCOMPLETE,
    PARSE_IN_PROGRESS,
    PARSE_CONTINUE,
    PARSE_INCOMPLETE,
    QUERY_COMPLETE,
    LIMIT_MAXED_OUT,
    BLUESKY_COLUMNS_TO_KEEP,
    TRUTH_COLUMNS_TO_KEEP,
)
from ..log import logger
from ..settings import API_URL


class QueryService:
    _query_repo: QueryRepository
    _query_term_repo: QueryTermRepository
    _query_request_repo: QueryRequestRepository
    _query_limit_repo: QueryLimitRepository
    _emitter: EventEmitter

    def __init__(
        self,
        query_repo: QueryRepository,
        query_term_repo: QueryTermRepository,
        query_request_repo: QueryRequestRepository,
        query_limit_repo: QueryLimitRepository,
        emitter: EventEmitter,
    ) -> None:
        self._emitter = emitter
        self._query_repo = query_repo
        self._query_term_repo = query_term_repo
        self._query_request_repo = query_request_repo
        self._query_limit_repo = query_limit_repo

    def _fetch_data(self, query: Query) -> None:
        if query.status == FETCH_CONTINUE:
            query.status = FETCH_IN_PROGRESS

            self._query_repo.update(query)
            self._emitter.emit(
                FETCH_UPDATE_PROGRESS,
                payload=Event(
                    data=QuerySerializer.model_validate(query).model_dump(mode="json")
                ),
            )

        if query.status == FETCH_INCOMPLETE:
            return

        limit = self._query_limit_repo.find()

        if limit is None:
            return

        logger.debug(
            "limit - count: %d last_fetch: %s",
            limit.count,
            limit.previous_request_date.isoformat()
            if limit.previous_request_date is not None
            else "None",
        )
        logger.debug(
            "query info - PLATFORM: %s STATUS: %s TERM: %s",
            query.platform,
            query.status,
            query.term,
        )

        localized_start_date = query.start_date.replace(
            tzinfo=(ZoneInfo(query.timezone))
        )
        localized_end_date = query.end_date.replace(tzinfo=(ZoneInfo(query.timezone)))
        params = {
            "site": query.platform,
            "term": query.term,
            "since": query.current_timestamp.replace(
                tzinfo=(ZoneInfo(query.timezone))
            ).strftime("%Y-%m-%dT%H:%M:%S.%f")
            if query.current_timestamp is not None
            else localized_start_date.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "until": localized_end_date.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "limit": 10000,
            "querytype": "boolean_content",
        }
        query_range = (localized_end_date - localized_start_date).total_seconds() / 3600

        logger.debug("request params: %s", params)

        while True:
            try:
                if limit.count == 0:
                    query.status = FETCH_INCOMPLETE

                    self._query_repo.update(query)
                    self._emitter.emit(
                        LIMIT_MAXED_OUT,
                        payload=Event(
                            data=QuerySerializer.model_validate(query).model_dump(
                                mode="json"
                            ),
                            message="query limit has been maxed out until limit refresh",
                        ),
                    )
                    break

                response = get(API_URL, params=params)

                response.raise_for_status()

                data = response.json()
                hits = data.get("hits", {}).get("hits", [])

                query.set_updated_at()

                if not hits and query.current_timestamp is None:
                    query.percentage = 1.0
                    query.status = QUERY_COMPLETE

                    self._query_repo.update(query)
                    self._emitter.emit(
                        QUERY_COMPLETE,
                        payload=Event(
                            data=QuerySerializer.model_validate(query).model_dump(
                                mode="json"
                            ),
                            message="query is now complete",
                        ),
                    )
                    break

                hit_length = len(hits)
                request = QueryRequest(
                    row_count=hit_length, data=hits, query_id=query.id
                )

                limit.decrement()
                limit.set_timestamps()
                limit.set_percentage()
                self._query_request_repo.create(request)
                self._query_limit_repo.update(limit)

                query = self._query_repo.find_by_id(query.id)

                if query is None:
                    break

                query.rows_fetched += hit_length

                if hit_length < 10000:
                    query.percentage = 1.0
                    query.status = CLEAN_IN_PROGRESS

                    self._query_repo.update(query)
                    self._emitter.emit(
                        CLEAN_IN_PROGRESS,
                        payload=Event(
                            data=QuerySerializer.model_validate(query).model_dump(
                                mode="json"
                            ),
                            message="query is now complete. data cleaning is now in progress",
                        ),
                    )
                    break

                last_created_at = hits[-1]["_source"].get("createdAt")

                if not last_created_at:
                    print("No 'created_at' found in the last hit.")
                    query.percentage = 1.0
                    query.status = CLEAN_IN_PROGRESS

                    self._query_repo.update(query)
                    self._emitter.emit(
                        CLEAN_IN_PROGRESS,
                        payload=Event(
                            data=QuerySerializer.model_validate(query).model_dump(
                                mode="json"
                            ),
                            message="query is now complete. data cleaning is now in progress",
                        ),
                    )
                    break

                last_created_at_datetime = datetime.fromisoformat(last_created_at)
                fetch_range = (
                    last_created_at_datetime.replace(tzinfo=(ZoneInfo(query.timezone)))
                    - localized_start_date
                ).total_seconds() / 3600
                query.percentage = fetch_range / query_range
                query.current_timestamp = last_created_at_datetime

                if hit_length == 10000 and query.rows_fetched == 10000:
                    query.status = FETCH_INCOMPLETE

                    self._query_repo.update(query)
                    self._emitter.emit(
                        FETCH_INCOMPLETE,
                        payload=Event(
                            data=QuerySerializer.model_validate(query).model_dump(
                                mode="json"
                            ),
                            message="data fetch is imcomplete. user must approve finishing the query to continue",
                        ),
                    )
                    break

                params["since"] = last_created_at

                self._query_repo.update(query)
                self._emitter.emit(
                    FETCH_UPDATE_PROGRESS,
                    payload=Event(
                        data=QuerySerializer.model_validate(query).model_dump(
                            mode="json"
                        )
                    ),
                )

            except Exception as e:
                logger.error(e, exc_info=True)
                break

    def _clean_data(self, query: Query) -> None:
        if query.status == CLEAN_CONTINUE:
            query.status = CLEAN_IN_PROGRESS
            self._query_repo.update(query)

        if query.status == CLEAN_INCOMPLETE:
            return

        for request in query.requests:
            cleaned_data = []

            for hit in request.data:
                source = hit["_source"]

                if source.get("embed") and source["embed"].get("external"):
                    if source["embed"]["external"].get("description") is not None:
                        source["embed"]["external"]["description"] = "␣"
                        clean_text(source["embed"]["external"]["description"])

                    if source["embed"]["external"].get("title") is not None:
                        source["embed"]["external"]["title"] = "␣"
                        clean_text(source["embed"]["external"]["title"])

                if source.get("text") is not None:
                    source["text"] = clean_text(source["text"])

                cleaned_data.append(source)

            request.cleaned_data = cleaned_data
            self._query_request_repo.update(request)

        query.status = PARSE_IN_PROGRESS

        self._query_repo.update(query)
        self._emitter.emit(
            PARSE_IN_PROGRESS,
            payload=Event(
                data=query,
                message="data cleaning is complete. parsing is now in progress",
            ),
        )

    def _parse_data(self, query: Query) -> None:
        if query.status == PARSE_CONTINUE:
            query.status = PARSE_IN_PROGRESS
            self._query_repo.update(query)

        if query.status == PARSE_INCOMPLETE:
            return

        data_frame: DataFrame = query.from_requests_to_dataframe()

        if query.platform == "bluesky":
            data_frame = data_frame[BLUESKY_COLUMNS_TO_KEEP]

        if query.platform == "truth_social":
            data_frame = data_frame[TRUTH_COLUMNS_TO_KEEP]

        data_frame.columns = data_frame.columns.str.replace("_source.", "", regex=False)
        query.status = QUERY_COMPLETE

        query.from_dataframe_to_processed_data(data_frame)
        self._query_repo.update(query)
        self._emitter.emit(
            QUERY_COMPLETE, payload=Event(data=query, message="query is now complete")
        )

    def process_query(self, id: UUID) -> None:
        async def func() -> None:
            query = self._query_repo.find_by_id(id)

            if query is None:
                return

            if query.status in [FETCH_CONTINUE, FETCH_IN_PROGRESS]:
                logger.debug("data fetch for query: %s is starting", query.id)
                await to_thread(self._fetch_data, query)
                logger.debug("data fetch for query: %s is complete", query.id)
                query = self._query_repo.find_by_id(id)

                if query is None:
                    return

            if query.status in [CLEAN_CONTINUE, CLEAN_IN_PROGRESS]:
                await to_thread(self._clean_data, query)
                query = self._query_repo.find_by_id(id)

                if query is None:
                    return

            if query.status in [PARSE_CONTINUE, PARSE_IN_PROGRESS]:
                await to_thread(self._parse_data, query)
                query = self._query_repo.find_by_id(id)

                if query is None:
                    return

            logger.debug(
                "applicable processing tasks for query: %s are complete", query.id
            )
            logger.debug(
                "Query - PLATFORM: %s STATUS: %s PROGRESS: %d ROWS FETCHED: %d",
                query.platform,
                query.status,
                query.percentage,
                query.rows_fetched,
            )

        task = create_task(func())

        @EventLinker.once(f"CANCEL:{str(id)}")
        def handle_task_cancel() -> None:
            logger.debug("Cancelling processing task for query: %s", str(id))

            if not task.done():
                task.cancel()

    def get(self, imcomplete_only: bool = False) -> list[Query]:
        return self._query_repo.find_all(imcomplete_only)

    def get_by_id(self, id: UUID) -> Query | None:
        return self._query_repo.find_by_id(id)

    def get_by_status(self, status: str) -> list[Query]:
        return self._query_repo.find_by_status(status)

    def get_by_platform(
        self, platform: str, imcomplete_only: bool = False
    ) -> list[Query]:
        return self._query_repo.find_by_platform(platform, imcomplete_only)

    def create(self, data: CreateQueryValidator) -> Query:
        query = Query(
            start_date=data.start_date, end_date=data.end_date, platform=data.platform
        )

        if data.timezone is not None:
            query.timezone = data.timezone

        self._query_repo.create(query)

        terms = [QueryTerm(query_id=query.id, term=data.term)]

        if data.term_modifiers is not None and len(data.term_modifiers) > 0:
            terms.extend(
                [
                    QueryTerm(
                        query_id=query.id,
                        modifier=term_modifier.modifier,
                        term=term_modifier.term,
                    )
                    for term_modifier in data.term_modifiers
                ]
            )

        self._query_term_repo.batch_create(terms)
        self.process_query(query.id)

        return query

    def update(self, id: UUID, data: UpdateQueryValidator) -> Query | None:
        query = self._query_repo.find_by_id(id)

        if query is None:
            return None

        if query.status == FETCH_INCOMPLETE and data.status == FETCH_CONTINUE:
            query.status = FETCH_CONTINUE

        if query.status == CLEAN_INCOMPLETE and data.status == CLEAN_CONTINUE:
            query.status = CLEAN_CONTINUE

        if query.status == PARSE_INCOMPLETE and data.status == PARSE_CONTINUE:
            query.status = PARSE_IN_PROGRESS

        self._emitter.emit(f"CANCEL:{str(query.id)}")
        self._query_repo.update(query)
        self.process_query(query.id)

        return query

    def delete(self, data: ParamValidator) -> None:
        if not self._query_repo.exists(data.id):
            return

        self._emitter.emit(f"CANCEL:{str(data.id)}")
        self._query_repo.delete(data.id)

    def batch_delete(self, data: DeleteQueriesValidator) -> None:
        ids: list[UUID] = []

        for id in data.ids:
            if not self._query_repo.exists(id):
                continue

            self._emitter.emit(f"CANCEL:{str(id)}")
            ids.append(id)

        self._query_repo.batch_delete(ids)

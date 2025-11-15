from pandas import DataFrame
from sqlalchemy.orm import joinedload
from requests import get, HTTPError, codes
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
    TermValidator,
    ParamValidator,
)
from ..serializers import QuerySerializer, QueryLimitSerializer
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
    LIMIT_UPDATE,
    PLATFORMS,
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

    def _fetch_data(self, query: Query) -> Query | None:
        if query.status == FETCH_CONTINUE:
            logger.debug("Fetch is being continued...")
            query.status = FETCH_IN_PROGRESS

            query.set_updated_at()

            query = self._query_repo.update(query)

            logger.debug(
                "continued query has been updated - id: %s status: %s",
                query.id,
                query.status,
            )
            self._emitter.emit(
                FETCH_UPDATE_PROGRESS,
                payload=Event(data=QuerySerializer.convert_model_to_dict(query)),
            )

        if query.status == FETCH_INCOMPLETE:
            return None

        limit = self._query_limit_repo.find()

        if limit is None:
            return None

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
                if (limit.limit_refresh_date is not None) and (
                    datetime.now() > limit.limit_refresh_date
                ):
                    limit.reset()

                    limit = self._query_limit_repo.update(limit)

                    logger.debug("limit reset has been triggered.")
                    self._emitter.emit(
                        LIMIT_UPDATE,
                        payload=Event(
                            data=QueryLimitSerializer.convert_model_to_dict(limit)
                        ),
                    )

                if limit.count == 0:
                    query.status = FETCH_INCOMPLETE

                    query.set_updated_at()

                    self._query_repo.update(query, True)
                    self._emitter.emit(
                        LIMIT_MAXED_OUT,
                        payload=Event(
                            data=QueryLimitSerializer.convert_model_to_dict(limit),
                            message="query limit has been maxed out until limit refresh",
                        ),
                    )
                    self._emitter.emit(
                        FETCH_INCOMPLETE,
                        payload=Event(
                            data=QuerySerializer.convert_model_to_dict(query),
                            message="data fetch is imcomplete. query has been paused due to limit being exhausted",
                        ),
                    )

                    break

                response = get(API_URL, params=params)

                response.raise_for_status()

                data = response.json()
                hits = data.get("hits", {}).get("hits", [])

                if not hits and query.current_timestamp is None:
                    query.percentage = 1.0
                    query.status = QUERY_COMPLETE

                    query.set_updated_at()

                    query = self._query_repo.update(query, True)

                    self._emitter.emit(
                        QUERY_COMPLETE,
                        payload=Event(
                            data=QuerySerializer.convert_model_to_dict(query),
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

                limit = self._query_limit_repo.update(limit)

                logger.debug(
                    "limit details after update - count: %d last_update: %s",
                    limit.count,
                    limit.limit_refresh_date.isoformat()
                    if limit.limit_refresh_date is not None
                    else "None",
                )
                self._emitter.emit(
                    LIMIT_UPDATE,
                    payload=Event(
                        data=QueryLimitSerializer.convert_model_to_dict(limit)
                    ),
                )

                query.rows_fetched += hit_length

                query.increment_queries_used()

                if hit_length < 10000:
                    query.percentage = 1.0
                    query.status = CLEAN_IN_PROGRESS

                    query.set_updated_at()

                    query = self._query_repo.update(query, True)

                    self._emitter.emit(
                        CLEAN_IN_PROGRESS,
                        payload=Event(
                            data=QuerySerializer.convert_model_to_dict(query),
                            message="data fetch is now complete. data cleaning is now in progress",
                        ),
                    )
                    break

                timestamp_column = PLATFORMS.get(query.platform, {}).get(
                    "created_at_column", None
                )

                if timestamp_column is None:
                    raise ValueError(
                        f"Unknown platform being used during _fetch_data function call platform: {query.platform}"
                    )

                last_created_at = hits[-1]["_source"].get(timestamp_column)

                if not last_created_at:
                    query.percentage = 1.0
                    query.status = CLEAN_IN_PROGRESS

                    query.set_updated_at()

                    query = self._query_repo.update(query, True)

                    self._emitter.emit(
                        CLEAN_IN_PROGRESS,
                        payload=Event(
                            data=QuerySerializer.convert_model_to_dict(query),
                            message="data fetch is now complete. data cleaning is now in progress",
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

                    query.set_updated_at()

                    query = self._query_repo.update(query, True)

                    self._emitter.emit(
                        FETCH_INCOMPLETE,
                        payload=Event(
                            data=QuerySerializer.convert_model_to_dict(query),
                            message="data fetch is imcomplete. user must approve finishing the query to continue",
                        ),
                    )
                    break

                params["since"] = last_created_at

                query.set_updated_at()

                query = self._query_repo.update(query, True)

                self._emitter.emit(
                    FETCH_UPDATE_PROGRESS,
                    payload=Event(
                        data=QuerySerializer.convert_model_to_dict(query),
                    ),
                )

            except HTTPError as err:
                if err.response.status_code != codes.too_many_requests or query is None:
                    logger.error(err, exc_info=True)
                    break

                query.status = FETCH_INCOMPLETE
                limit.count = 0

                limit.set_timestamps()
                limit.set_percentage()
                query.set_updated_at()
                self._query_repo.update(query, True)

                limit = self._query_limit_repo.update(limit)

                self._emitter.emit(
                    LIMIT_MAXED_OUT,
                    payload=Event(
                        data=QueryLimitSerializer.convert_model_to_dict(limit),
                        message="query limit has been maxed out until limit refresh",
                    ),
                )
                self._emitter.emit(
                    FETCH_INCOMPLETE,
                    payload=Event(
                        data=QuerySerializer.convert_model_to_dict(query),
                        message="data fetch is imcomplete. query has been paused due to limit being exhausted",
                    ),
                )
                break

            except Exception as e:
                logger.error(e, exc_info=True)
                break

        query = self._query_repo.find_by_id(
            query.id, [joinedload(Query.terms), joinedload(Query.requests)]
        )

        return query

    def _clean_data(self, query: Query) -> Query | None:
        if query.status == CLEAN_CONTINUE:
            query.status = CLEAN_IN_PROGRESS
            query = self._query_repo.update(query, True)

        if query.status == CLEAN_INCOMPLETE:
            return None

        try:
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

                request.set_updated_at()
                self._query_request_repo.update(request)

            query.status = PARSE_IN_PROGRESS
            query.set_updated_at()

            query = self._query_repo.update(query, True)
            query = self._query_repo.find_by_id(
                query.id, [joinedload(Query.requests), joinedload(Query.terms)]
            )

            if query is None:
                return None

            self._emitter.emit(
                PARSE_IN_PROGRESS,
                payload=Event(
                    data=QuerySerializer.convert_model_to_dict(query),
                    message="data cleaning is complete. parsing is now in progress",
                ),
            )

            return query

        except Exception as err:
            logger.error(err, exc_info=True)
            return None

    def _parse_data(self, query: Query) -> Query | None:
        logger.debug(f"_parse_data called for query {query.id}, status: {query.status}")

        if query.status == PARSE_CONTINUE:
            query.status = PARSE_IN_PROGRESS
            query = self._query_repo.update(query, True)

        if query.status == PARSE_INCOMPLETE:
            return None

        try:
            logger.debug("Creating dataframe from requests...")
            data_frame: DataFrame = query.from_requests_to_dataframe()
            logger.debug(f"Dataframe created with {len(data_frame)} rows")

            dataframe_columns = PLATFORMS.get(query.platform, {}).get("columns", None)

            if dataframe_columns is None:
                raise ValueError(
                    f"Unknown platform is being used during _parse_data function call platform: {query.platform}"
                )

            available_columns = [
                column for column in dataframe_columns if column in data_frame.columns
            ]
            data_frame = data_frame[available_columns]

            logger.debug("Converting to processed data...")
            query.from_dataframe_to_processed_data(data_frame)
            query.status = QUERY_COMPLETE
            query.set_updated_at()

            query = self._query_repo.update(query, True)

            self._emitter.emit(
                QUERY_COMPLETE,
                payload=Event(
                    data=QuerySerializer.convert_model_to_dict(query),
                    message="query is now complete",
                ),
            )

            return query

        except Exception as err:
            logger.error(err, exc_info=True)
            return None

    def process_query(self, id: UUID) -> None:
        async def func() -> None:
            query = self._query_repo.find_by_id(
                id, [joinedload(Query.terms), joinedload(Query.requests)]
            )

            if query is None:
                return

            if query.status in [FETCH_CONTINUE, FETCH_IN_PROGRESS]:
                logger.debug(
                    "data fetch for query is starting - id: %s status: %s",
                    query.id,
                    query.status,
                )
                query = await to_thread(self._fetch_data, query)

                if query is None:
                    return

                logger.debug("data fetch for query: %s is complete", query.id)

            if query.status in [CLEAN_CONTINUE, CLEAN_IN_PROGRESS]:
                query = await to_thread(self._clean_data, query)

                if query is None:
                    return

            if query.status in [PARSE_CONTINUE, PARSE_IN_PROGRESS]:
                query = await to_thread(self._parse_data, query)

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
            if task.done():
                return

            logger.debug("Cancelling processing task for query: %s", str(id))
            task.cancel()

    def get(self, include_requests: bool = False) -> list[Query]:
        if include_requests:
            return self._query_repo.find_all(
                [joinedload(Query.terms), joinedload(Query.requests)]
            )

        return self._query_repo.find_all()

    def get_by_id(self, id: UUID, incldue_requests: bool = False) -> Query | None:
        if incldue_requests:
            return self._query_repo.find_by_id(
                id, [joinedload(Query.terms), joinedload(Query.requests)]
            )

        return self._query_repo.find_by_id(id)

    def get_by_status(self, status: str, include_requests: bool = False) -> list[Query]:
        if include_requests:
            return self._query_repo.find_by_status(
                status, [joinedload(Query.terms), joinedload(Query.requests)]
            )

        return self._query_repo.find_by_status(status)

    def get_by_platform(
        self, platform: str, incldue_requests: bool = False
    ) -> list[Query]:
        if incldue_requests:
            return self._query_repo.find_by_platform(
                platform, [joinedload(Query.terms), joinedload(Query.requests)]
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
            query.id, [joinedload(Query.terms), joinedload(Query.requests)]
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

        if (query.status == CLEAN_INCOMPLETE and data.status == CLEAN_CONTINUE) or (
            query.status == FETCH_INCOMPLETE and data.status == CLEAN_CONTINUE
        ):
            query.status = CLEAN_CONTINUE

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

    def batch_delete(self, data: DeleteQueriesValidator) -> None:
        ids: list[UUID] = []

        for id in data.ids:
            if not self._query_repo.exists(id):
                continue

            self._emitter.emit(f"CANCEL:{str(id)}")
            ids.append(id)

        self._query_repo.batch_delete(ids)

from ..settings import API_URL
from ..db.models import Query, QueryTerm, QueryRequest
from ..db.repositories import (
    QueryRespository,
    QueryTermRepository,
    QueryRequestRepository,
    QueryLimitRepository,
)
from ..validator import CreateQueryValidator, UpdateQueryValidator, ParamValidator
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
from requests import get
from pyventus import AsyncIOEventEmitter
from asyncio import run
from datetime import datetime
from typing import List


class QueryService:
    _query_repo: QueryRespository
    _query_term_repo: QueryTermRepository
    _query_request_repo: QueryRequestRepository
    _query_limit_repo: QueryLimitRepository
    _emitter: AsyncIOEventEmitter

    def __init__(
        self,
        query_repo: QueryRespository,
        query_term_repo: QueryTermRepository,
        query_request_repo: QueryRequestRepository,
        query_limit_repo: QueryLimitRepository,
        emitter: AsyncIOEventEmitter,
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
            self._emitter.emit(FETCH_UPDATE_PROGRESS,
                               payload=Event(data=query))

        if query.status == FETCH_INCOMPLETE:
            return

        limit = self._query_limit_repo.find()
        params = {
            "site": query.platform,
            "term": query.term,
            "since": query.current_timestamp
            if query.current_timestamp is not None
            else query.start_date,
            "until": query.end_date,
            "limit": 10000,
            "querytype": "boolean_content",
        }
        query_range = (query.end_date -
                       query.start_date).total_seconds() / 3600

        while True:
            try:
                if limit.count == 0:
                    query.status = FETCH_INCOMPLETE

                    self._query_repo.update(query)
                    self._emitter.emit(
                        LIMIT_MAXED_OUT,
                        payload=Event(
                            data=query,
                            message="query limit has been maxed out until limit refresh",
                        ),
                    )
                    break

                response = get(API_URL, params=params)

                response.raise_for_status()

                data = response.json()
                hits = data.get("hits", {}).get("hits", [])

                query.set_updated_at()

                if not hits:
                    query.percentage = 1.0
                    query.status = QUERY_COMPLETE

                    self._query_repo.update(query)
                    self._emitter.emit(
                        QUERY_COMPLETE,
                        payload=Event(
                            data=query,
                            message="query is now complete",
                        ),
                    )
                    break

                hit_length = len(hits)
                query.rows_fetched += hit_length
                request = QueryRequest(
                    row_count=hit_length, data=hits, query_ID=query.id
                )

                limit.decrement()
                limit.set_timestamps()
                self._query_request_repo.create(request)
                self._query_limit_repo.update(limit)
                query.requests.append(request)

                if hit_length < 10000:
                    query.percentage = 1.0
                    query.status = CLEAN_IN_PROGRESS

                    self._query_repo.update(query)
                    self._emitter.emit(
                        CLEAN_IN_PROGRESS,
                        payload=Event(
                            data=query,
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
                            data=query,
                            message="query is now complete. data cleaning is now in progress",
                        ),
                    )
                    break

                fetch_range = (
                    datetime.fromisoformat(last_created_at) - query.start_date
                ).total_seconds() / 3600
                query.percentage = (fetch_range / query_range) * 100
                query.current_timestamp = last_created_at

                if hit_length == 10000 and query.rows_fetched == 10000:
                    query.status = FETCH_INCOMPLETE

                    self._query_repo.update(query)
                    self._emitter.emit(
                        FETCH_INCOMPLETE,
                        payload=Event(
                            data=query,
                            message="data fetch is imcomplete. user must approve finishing the query to continue",
                        ),
                    )
                    break

                print(last_created_at)
                params["since"] = last_created_at

                self._query_repo.update(query)
                self._emitter.emit(FETCH_UPDATE_PROGRESS,
                                   payload=Event(data=query))

            except Exception as e:
                print(f"Error occurred: {e}")
                break

    def _clean_data(self, query: Query) -> None:
        if query.status == CLEAN_CONTINUE:
            query.status = CLEAN_IN_PROGRESS
            self._query_repo.update(query)

        if query.status == CLEAN_INCOMPLETE:
            return

        for hit in query.requests:
            source = hit.data["_source"]

            if source.get("embed") and source["embed"].get("external"):
                if source["embed"]["external"].get("description") is not None:
                    source["embed"]["external"]["description"] = "␣"
                    clean_text(source["embed"]["external"]["description"])

                if source["embed"]["external"].get("title") is not None:
                    source["embed"]["external"]["title"] = "␣"
                    clean_text(source["embed"]["external"]["title"])

            if source.get("text") is not None:
                source["text"] = clean_text(source["text"])

            hit.cleaned_data = source
            self._query_request_repo.update(hit)

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

        data_frame = query.from_requests_to_dataframe()

        if query.platform == "bluesky":
            data_frame = data_frame[BLUESKY_COLUMNS_TO_KEEP]

        if query.platform == "truth_social":
            data_frame = data_frame[TRUTH_COLUMNS_TO_KEEP]

        data_frame.columns = data_frame.columns.str.replace(
            "_source.", "", regex=False)
        query.status = QUERY_COMPLETE

        query.from_dataframe_to_processed_data(data_frame)
        self._query_repo.update(query)
        self._emitter.emit(
            QUERY_COMPLETE, payload=Event(
                data=query, message="query is now complete")
        )

    def process_query(self, query: Query) -> None:
        async def func() -> None:
            if query.status in [FETCH_CONTINUE, FETCH_IN_PROGRESS]:
                self._fetch_data(query)

            if query.status in [CLEAN_CONTINUE, CLEAN_IN_PROGRESS]:
                self._clean_data(query)

            if query.status in [PARSE_CONTINUE, PARSE_IN_PROGRESS]:
                self._parse_data(query)

        run(func())

    def get(self, imcomplete_only: bool = False) -> List[Query]:
        return self._query_repo.find_all(imcomplete_only)

    def get_by_id(self, id: str) -> Query:
        return self._query_repo.find_by_id(id)

    def get_by_status(self, status: str) -> List[Query]:
        return self._query_repo.find_by_status(status)

    def get_by_platform(
        self, platform: str, imcomplete_only: bool = False
    ) -> List[Query]:
        return self._query_repo.find_by_platform(platform, imcomplete_only)

    def create(self, data: CreateQueryValidator) -> Query:
        query = Query(
            start_date=data.start_data, end_date=data.end_date, platform=data.platform
        )

        if data.timezone is not None:
            query.timezone = data.timezone

        self._query_repo.create(query)

        terms = [QueryTerm(query_id=query, term=data.term)]

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
        query.terms.extend(terms)
        self.process_query(query)

        return query

    def update(self, id: str, data: UpdateQueryValidator) -> Query:
        query = self._query_repo.find_by_id(id)

        if query is None:
            return None

        if query.status == FETCH_INCOMPLETE and data.status == FETCH_CONTINUE:
            query.status = FETCH_CONTINUE

        if query.status == CLEAN_INCOMPLETE and data.status == CLEAN_CONTINUE:
            query.status = CLEAN_CONTINUE

        if query.status == PARSE_INCOMPLETE and data.status == PARSE_CONTINUE:
            query.status = PARSE_IN_PROGRESS

        self._query_repo.update(query)
        self.process_query(query)

        return query

    def delete(self, data: ParamValidator) -> None:
        pass

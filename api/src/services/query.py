from ..settings import API_URL
from ..db.models import Query, QueryTerm, QueryRequest, QueryLimit
from ..db.repositories import (
    QueryRespository,
    QueryTermRepository,
    QueryRequestRepository,
    QueryLimitRepository,
)
from ..utils.sanitize import clean_text
from requests import get
from pyventus import AsyncIOEventEmitter
from asyncio import run


class QueryService:
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
        params = {
            "site": query.platform,
            "term": term,
            "since": query.start_date,
            "until": query.end_date,
            "limit": 10000,
            "querytype": "boolean_content",
        }

        while True:
            try:
                response = get(API_URL, params=params)
                response.raise_for_status()  # error for any http issues
                data = response.json()
                hits = data.get("hits", {}).get("hits", [])

                if not hits:
                    all_hits.extend(hits)

                if len(hits) < 10000:
                    break

                last_created_at = hits[-1]["_source"].get(field)

                if not last_created_at:
                    print("No 'created_at' found in the last hit.")
                    break

                print(last_created_at)
                params["since"] = last_created_at

            except Exception as e:
                print(f"Error occurred: {e}")
                break

    def _clean_data(self, query: Query) -> None:
        for hit in query.requests:
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

        query.status = "PARSE:IN_PROGRESS"

    def _parse_data(self, query: Query) -> None:
        pass

    def process_query(self, query: Query) -> None:
        async def func() -> None:
            if query.status in ["FETCH:CONTINUE", "FETCH:IN_PROGRESS"]:
                self._fetch_data(query)

            if query.status in ["CLEAN:CONTINUE", "CLEAN:IN_PROGRESS"]:
                self._clean_data(query)

            if query.status in ["PARSE:CONTINUE", "PARSE:IN_PROGRESS"]:
                self._parse_data(query)

        run(func())

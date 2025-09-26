from ..db.models import QueryLimit
from ..db.repositories import QueryLimitRepository
from ..validator import CreateQueryValidator, UpdateQueryValidator


class QueryLimitService:
    _query_limit_repo: QueryLimitRepository

    def __init__(self, query_limit_repo: QueryLimitRepository) -> None:
        self._query_limit_repo = query_limit_repo

    def get(self) -> QueryLimit:
        return self._query_limit_repo.find()

    def create(self, data: CreateQueryValidator) -> QueryLimit:
        limit = QueryLimit(
            count=data.count,
            previous_request_date=data.previous_request_date,
            limit_refresh_date=data.limit_refresh_date,
        )

        self._query_limit_repo.create(limit)

        return limit

    def update(self, data: UpdateQueryValidator) -> QueryLimit:
        limit = self._query_limit_repo.find()

        if data.count is not None and limit.count != data.count:
            limit.count = data.count

        if (
            data.previous_request_date is not None
            and limit.previous_request_date != data.previous_request_date
        ):
            limit.previous_request_date = data.previous_request_date

        if (
            data.limit_refresh_date is not None
            and limit.limit_refresh_date != data.limit_refresh_date
        ):
            limit.limit_refresh_date = data.limit_refresh_date

        self._query_limit_repo.update(limit)

        return limit

    def delete(self) -> None:
        self._query_limit_repo.delete()

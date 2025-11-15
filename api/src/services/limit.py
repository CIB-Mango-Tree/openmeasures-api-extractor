from datetime import datetime
from pyventus.events import EventEmitter
from ..db.models import QueryLimit
from ..db.repositories import QueryLimitRepository
from ..serializers import QueryLimitSerializer
from ..event import Event
from ..utils.constants import LIMIT_UPDATE


class QueryLimitService:
    _query_limit_repo: QueryLimitRepository
    _emitter: EventEmitter

    def __init__(
        self, query_limit_repo: QueryLimitRepository, emitter: EventEmitter
    ) -> None:
        self._query_limit_repo = query_limit_repo
        self._emitter = emitter

    def get(self) -> QueryLimit | None:
        return self._query_limit_repo.find()

    def maintain_and_check(self) -> None:
        limit: QueryLimit | None = self._query_limit_repo.find()

        if limit is None:
            limit = self._query_limit_repo.create(QueryLimit())

        if (
            limit.limit_refresh_date is None
            or datetime.now() < limit.limit_refresh_date
        ):
            return

        limit.reset()
        limit = self._query_limit_repo.update(limit)
        self._emitter.emit(
            LIMIT_UPDATE,
            payload=Event(data=QueryLimitSerializer.convert_model_to_dict(limit)),
        )

    def delete(self) -> None:
        self._query_limit_repo.delete()

from datetime import datetime
from pyventus.events import EventEmitter
from ...db.models import QueryLimit
from ...db.repositories import QueryLimitRepository
from ...event import Event
from ...log import logger
from ...serializers import QueryLimitSerializer
from ...utils.constants import LIMIT_MAXED_OUT, LIMIT_UPDATE


class QuotaTracker:
    """Owns the request-quota ledger and its LIMIT:* events.

    Split out of the fetch loop, which was simultaneously paging the API, tracking the quota and
    driving the query state machine.
    """

    def __init__(self, limit_repo: QueryLimitRepository, emitter: EventEmitter) -> None:
        self._limit_repo = limit_repo
        self._emitter = emitter

    def load(self) -> QueryLimit | None:
        return self._limit_repo.find()

    def _emit(self, event: str, limit: QueryLimit, message: str | None = None) -> None:
        self._emitter.emit(
            event,
            payload=Event(
                data=QueryLimitSerializer.convert_model_to_dict(limit), message=message
            ),
        )

    def refresh_if_due(self, limit: QueryLimit) -> QueryLimit:
        if limit.limit_refresh_date is None or datetime.now() <= limit.limit_refresh_date:
            return limit

        limit.reset()

        limit = self._limit_repo.update(limit)

        logger.debug("limit reset has been triggered.")
        self._emit(LIMIT_UPDATE, limit)

        return limit

    @staticmethod
    def is_exhausted(limit: QueryLimit) -> bool:
        return limit.count == 0

    def consume(self, limit: QueryLimit) -> QueryLimit:
        """Records one spent request."""
        limit.decrement()
        limit.set_timestamps()
        limit.set_percentage()

        limit = self._limit_repo.update(limit)

        logger.debug(
            "limit details after update - count: %d last_update: %s",
            limit.count,
            limit.limit_refresh_date.isoformat()
            if limit.limit_refresh_date is not None
            else "None",
        )
        self._emit(LIMIT_UPDATE, limit)

        return limit

    def exhaust(self, limit: QueryLimit) -> QueryLimit:
        """Marks the quota as spent because the API said so (HTTP 429)."""
        limit.count = 0

        limit.set_timestamps()
        limit.set_percentage()

        return self._limit_repo.update(limit)

    def announce_exhausted(self, limit: QueryLimit) -> None:
        self._emit(
            LIMIT_MAXED_OUT,
            limit,
            "query limit has been maxed out until limit refresh",
        )

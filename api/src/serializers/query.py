from pydantic import UUID4
from datetime import datetime
from .base import BaseSerializer
from .term import QueryTermSerializer


class QuerySerializer(BaseSerializer):
    id: UUID4
    created_at: datetime
    updated_at: datetime | None = None
    status: str
    timezone: str | None = None
    start_date: datetime
    end_date: datetime
    current_timestamp: datetime | None = None
    platform: str
    rows_fetched: int
    queries_used: int
    percentage: float
    terms: list[QueryTermSerializer] = []

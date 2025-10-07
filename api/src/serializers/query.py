from pydantic import BaseModel, ConfigDict, UUID4
from datetime import datetime
from .term import QueryTermSerializer
from .request import QueryRequestSerializer


class QuerySerializer(BaseModel):
    model_config = ConfigDict(from_attributes=True)
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
    percentage: float
    terms: list[QueryTermSerializer] = []
    requests: list[QueryRequestSerializer] = []

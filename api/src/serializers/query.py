from pydantic import BaseModel, ConfigDict, UUID
from datetime import datetime
from .term import QueryTermSerializer
from .request import QueryRequestSerializer
from typing import List, Optional


class QuerySerializer(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: str
    timezone: Optional[str] = None
    start_date: datetime
    end_date: datetime
    current_timestamp: Optional[datetime] = None
    platform: str
    rows_fetched: int
    percentage: float
    terms: List[QueryTermSerializer] = []
    requests: List[QueryRequestSerializer] = []

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class QueryLimitSerializer(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    count: int
    percentage: float
    previous_request_date: Optional[datetime] = None
    limit_refresh_date: Optional[datetime] = None

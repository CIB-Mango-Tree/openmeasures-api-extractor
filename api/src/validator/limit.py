from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class CreateLimitValidator(BaseModel):
    count: float = Field(gte=0)
    previous_request_date: Optional[datetime] = None
    limit_refresh_date: Optional[datetime] = None


class UpdateLimitValidator(BaseModel):
    count: Optional[float] = Field(gte=0)
    previous_request_date: Optional[datetime] = None
    limit_refresh_date: Optional[datetime] = None

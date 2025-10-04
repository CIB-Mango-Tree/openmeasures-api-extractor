from pydantic import BaseModel, Field
from datetime import datetime


class CreateLimitValidator(BaseModel):
    count: int = Field(ge=0)
    previous_request_date: datetime | None = None
    limit_refresh_date: datetime | None = None


class UpdateLimitValidator(BaseModel):
    count: int | None = Field(ge=0)
    previous_request_date: datetime | None = None
    limit_refresh_date: datetime | None = None

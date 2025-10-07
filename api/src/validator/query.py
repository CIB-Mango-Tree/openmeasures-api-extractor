from pydantic import BaseModel, Field, UUID4
from .term import TermValidator
from datetime import datetime


class CreateQueryValidator(BaseModel):
    platform: str = Field(min_length=1)
    term: str = Field(min_length=1)
    term_modifiers: list[TermValidator] = []
    start_date: datetime
    end_date: datetime
    timezone: str | None = datetime.now().astimezone().tzname()


class UpdateQueryValidator(BaseModel):
    status: str = Field(min_length=1)


class DeleteQueriesValidator(BaseModel):
    ids: list[UUID4]

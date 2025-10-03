from pydantic import BaseModel, Field, UUID4
from .term import TermValidator
from datetime import datetime
from typing import Optional, List


class CreateQueryValidator(BaseModel):
    platform: str = Field(min_length=1)
    term: str = Field(min_length=1)
    term_modifiers: Optional[List[TermValidator]] = None
    start_data: datetime = None
    end_date: datetime = None
    timezone: Optional[str] = datetime.now().astimezone().tzname()


class UpdateQueryValidator(BaseModel):
    status: str = Field(min_length=1)


class DeleteQueriesValidator(BaseModel):
    ids: List[UUID4]

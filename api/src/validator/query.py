from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict


class CreateQueryData(BaseModel):
    platform: str = Field(min_length=1)
    term: str = Field(min_length=1)
    term_modifiers: Optional[list[Dict[str, str]]] = None
    since: datetime = None
    until: datetime = None
    timezone: Optional[str] = datetime.now().astimezone().tzname()


class UpdateQueryData(BaseModel):
    status: str = Field(min_length=1)

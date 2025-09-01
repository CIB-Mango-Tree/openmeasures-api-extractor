from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict


class QueryData(BaseModel):
    site: str = Field(min_length=1)
    term: str = Field(min_length=1)
    term_modifiers: Optional[list[Dict[str, str]]] = None
    since: datetime = None
    until: datetime = None
    limit: int = Field(lte=390000)
    timezone: Optional[str] = datetime.now().astimezone().tzname()

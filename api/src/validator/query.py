from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Dict


class QueryData(BaseModel):
    site: str
    term: str
    term_modifiers: Optional[list[Dict[str, str]]] = None
    since: datetime =
    until: datetime =
    limit: int
    timezone: Optional[str] = datetime.now().astimezone().tzname()

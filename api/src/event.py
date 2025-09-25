from dataclasses import dataclass
from ..db.models import Query
from typing import Optional


@dataclass
class Event:
    message: Optional[str] = None
    data: Query

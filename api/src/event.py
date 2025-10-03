from dataclasses import dataclass
from .db.models import Query
from typing import Optional


@dataclass
class Event:
    data: Query
    message: Optional[str] = None

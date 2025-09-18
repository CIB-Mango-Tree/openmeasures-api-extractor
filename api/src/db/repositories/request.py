from .base import BaseRepository
from ..models import QueryRequest
from sqlalchemy import select
from typing import List


class QueryRequestRepository(BaseRepository[QueryRequest]):
    def find_by_query_id(self, id: str) -> List[QueryRequest]:
        return self._db.scalars(select(QueryRequest).where(QueryRequest.query_ID == id))

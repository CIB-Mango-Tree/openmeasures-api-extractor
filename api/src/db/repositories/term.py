from .base import BaseRepository
from ..models import QueryTerm
from sqlalchemy import select
from typing import List


class QueryTermRepository(BaseRepository[QueryTerm]):
    def find_by_query_id(self, id: str) -> List[QueryTerm]:
        return self._db.scalars(select(QueryTerm).where(QueryTerm.query_ID == id))

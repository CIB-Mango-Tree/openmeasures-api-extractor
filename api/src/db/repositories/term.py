from .base import BaseRepository
from ..models import QueryTerm
from sqlalchemy import select
from typing import List


class QueryTermRepository(BaseRepository[QueryTerm]):
    def find_by_query_id(self, id: str) -> List[QueryTerm]:
        return self._db.scalars(select(QueryTerm).where(QueryTerm.query_ID == id)).all()

    def batch_create(self, models: List[QueryTerm]) -> None:
        self._db.add_all(models)
        self._db.commit()

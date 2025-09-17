from .base import BaseRepository
from sqlalchemy import select
from ..models import Query
from typing import List


class QueryRepository(BaseRepository):
    def find_all(self, incomplete_only: bool = False) -> List[Query]:
        return self._db.scalars(select(Query)).all()

    def find_by_status(self, status: str) -> List[Query]:
        return self._db.scalars(select(Query).where(Query.status == status)).all()

    def find_by_platform(
        self, platform: str, incomplete_only: bool = False
    ) -> List[Query]:
        return self._db.scalars(select(Query).where(Query.platform == platform)).all()

    def create(self, query: Query) -> None:
        self._db.add(query)
        self._db.commit()

    def update(self, query: Query) -> None:
        pass

    def delete(self, id: str) -> None:
        query: Query = self._db.scalars(select(Query).where(Query.id == id)).one()

        if query is None:
            return

        self._db.delete(query)
        self._db.commit()

    def batch_delete(self, ids: List[str]) -> None:
        queries: List[Query] = self._db.scalars(
            select(Query).where(Query.id in ids)
        ).all()

        if len(queries) == 0:
            return

        self._db.delete(queries)
        self._db.commit()

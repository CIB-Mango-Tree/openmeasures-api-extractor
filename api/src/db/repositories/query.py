from .base import BaseRepository
from sqlalchemy import select
from ..models import Query
from typing import List


class QueryRepository(BaseRepository):
    def find_all(self, incomplete_only: bool = False) -> List[Query]:
        if incomplete_only:
            return self._db.scalars(
                select(Query).where(Query.status == "INCOMPLETE")
            ).all()

        return self._db.scalars(select(Query)).all()

    def find_by_status(self, status: str) -> List[Query]:
        return self._db.scalars(select(Query).where(Query.status == status)).all()

    def find_by_platform(
        self, platform: str, incomplete_only: bool = False
    ) -> List[Query]:
        if incomplete_only:
            return self._db.scalars(
                select(Query).where(
                    (Query.platform == platform) and (Query.status == "INCOMPLETE")
                )
            ).all()

        return self._db.scalars(select(Query).where(Query.platform == platform)).all()

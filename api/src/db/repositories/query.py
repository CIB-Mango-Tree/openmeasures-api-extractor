from .base import BaseRepository
from sqlalchemy import select, delete
from ..models import Query
from ...utils.constants import FETCH_INCOMPLETE, CLEAN_INCOMPLETE, PARSE_INCOMPLETE
from typing import List


class QueryRepository(BaseRepository[Query]):
    def find_all(self, incomplete_only: bool = False) -> List[Query]:
        if incomplete_only:
            return self._db.scalars(
                select(Query).where(
                    Query.status
                    in [FETCH_INCOMPLETE, CLEAN_INCOMPLETE, PARSE_INCOMPLETE]
                )
            ).all()

        return self._db.scalars(select(Query)).all()

    def find_by_id(self, id: str) -> Query:
        return self._db.scalars(select(Query).where(Query.id == id)).first()

    def find_by_status(self, status: str) -> List[Query]:
        return self._db.scalars(select(Query).where(Query.status == status)).all()

    def find_by_platform(
        self, platform: str, incomplete_only: bool = False
    ) -> List[Query]:
        if incomplete_only:
            return self._db.scalars(
                select(Query).where(
                    (Query.platform == platform)
                    and (
                        Query.status
                        in [FETCH_INCOMPLETE, CLEAN_INCOMPLETE, PARSE_INCOMPLETE]
                    )
                )
            ).all()

        return self._db.scalars(select(Query).where(Query.platform == platform)).all()

    def batch_delete(self, ids: List[str]) -> None:
        self._db.execute(delete(Query).where(Query.id.in_(ids)))
        self._db.commit()

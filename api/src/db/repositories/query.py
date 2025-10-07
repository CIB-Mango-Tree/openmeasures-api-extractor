from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from uuid import UUID
from .base import BaseRepository
from ..models import Query
from ...utils.constants import FETCH_INCOMPLETE, CLEAN_INCOMPLETE, PARSE_INCOMPLETE


class QueryRepository(BaseRepository[Query]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Query)

    def find_all(self, incomplete_only: bool = False) -> list[Query]:
        if incomplete_only:
            return list(
                self._db.scalars(
                    select(Query).where(
                        Query.status.in_(
                            [FETCH_INCOMPLETE, CLEAN_INCOMPLETE, PARSE_INCOMPLETE]
                        )
                    )
                ).all()
            )

        return list(self._db.scalars(select(Query)).all())

    def find_by_id(self, id: UUID) -> Query | None:
        return self._db.scalars(select(Query).where(Query.id == id)).first()

    def find_by_status(self, status: str) -> list[Query]:
        return list(self._db.scalars(select(Query).where(Query.status == status)).all())

    def find_by_platform(
        self, platform: str, incomplete_only: bool = False
    ) -> list[Query]:
        if incomplete_only:
            return list(
                self._db.scalars(
                    select(Query).where(
                        Query.platform == platform,
                        Query.status.in_(
                            [FETCH_INCOMPLETE, CLEAN_INCOMPLETE, PARSE_INCOMPLETE]
                        ),
                    )
                ).all()
            )

        return list(
            self._db.scalars(select(Query).where(Query.platform == platform)).all()
        )

    def batch_delete(self, ids: list[UUID]) -> None:
        self._db.execute(delete(Query).where(Query.id.in_(ids)))
        self._db.commit()

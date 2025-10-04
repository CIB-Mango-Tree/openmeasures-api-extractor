from sqlalchemy import select
from sqlalchemy.orm import Session
from .base import BaseRepository
from ..models import QueryTerm


class QueryTermRepository(BaseRepository[QueryTerm]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, QueryTerm)

    def find_by_query_id(self, id: str) -> list[QueryTerm]:
        return list(
            self._db.scalars(select(QueryTerm).where(QueryTerm.query_ID == id)).all()
        )

    def batch_create(self, models: list[QueryTerm]) -> None:
        self._db.add_all(models)
        self._db.commit()

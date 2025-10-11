from sqlalchemy import select
from sqlalchemy.orm import Session, scoped_session
from uuid import UUID
from .base import BaseRepository
from ..models import QueryTerm


class QueryTermRepository(BaseRepository[QueryTerm]):
    def __init__(self, factory: scoped_session[Session]) -> None:
        super().__init__(factory, QueryTerm)

    def find_by_query_id(self, id: UUID) -> list[QueryTerm]:
        session = self._get_session()

        return list(
            session.scalars(select(QueryTerm).where(QueryTerm.query_id == id)).all()
        )

    def batch_create(self, models: list[QueryTerm]) -> None:
        session = self._get_session()

        session.add_all(models)
        session.commit()

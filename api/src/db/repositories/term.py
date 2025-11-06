from sqlalchemy import select
from sqlalchemy.orm import Session, scoped_session
from uuid import UUID
from .base import BaseRepository
from ..models import QueryTerm


class QueryTermRepository(BaseRepository[QueryTerm]):
    def __init__(self, factory: scoped_session[Session]) -> None:
        super().__init__(factory, QueryTerm)

    def find_by_query_id(self, id: UUID) -> list[QueryTerm]:
        session: Session = self._session_factory()

        return list(
            session.scalars(
                select(QueryTerm)
                .where(QueryTerm.query_id == id)
                .execution_options(populate_existing=True)
            ).all()
        )

    def batch_create(self, models: list[QueryTerm]) -> None:
        session: Session = self._session_factory()

        session.add_all(models)
        session.commit()

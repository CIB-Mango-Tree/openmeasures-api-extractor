from sqlalchemy import select
from sqlalchemy.orm import Session, scoped_session
from uuid import UUID
from .base import BaseRepository
from ..models import QueryRequest


class QueryRequestRepository(BaseRepository[QueryRequest]):
    def __init__(self, factory: scoped_session[Session]) -> None:
        super().__init__(factory, QueryRequest)

    def find_by_query_id(self, id: UUID) -> list[QueryRequest]:
        session = self._get_session()

        return list(
            session.scalars(select(QueryRequest).where(QueryRequest.query_id == id))
        )

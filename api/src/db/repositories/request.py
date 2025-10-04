from sqlalchemy import select
from sqlalchemy.orm import Session
from .base import BaseRepository
from ..models import QueryRequest


class QueryRequestRepository(BaseRepository[QueryRequest]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, QueryRequest)

    def find_by_query_id(self, id: str) -> list[QueryRequest]:
        return list(
            self._db.scalars(select(QueryRequest).where(QueryRequest.query_ID == id))
        )

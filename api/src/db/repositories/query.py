from sqlalchemy import select, delete
from sqlalchemy.orm import Session, scoped_session, joinedload
from uuid import UUID
from .base import BaseRepository
from ..models import Query
from ...utils.constants import FETCH_INCOMPLETE, CLEAN_INCOMPLETE, PARSE_INCOMPLETE
from typing import Any

INCOMPLETE_STATUSES: list[str] = [FETCH_INCOMPLETE, CLEAN_INCOMPLETE, PARSE_INCOMPLETE]


class QueryRepository(BaseRepository[Query]):
    def __init__(self, factory: scoped_session[Session]) -> None:
        super().__init__(factory, Query)

    def find_all(
        self, query_options: list[Any] = [joinedload(Query.terms)]
    ) -> list[Query]:
        session = self._get_session()

        return list(session.scalars(select(Query).options(*query_options)).unique())

    def find_by_id(
        self, id: UUID, query_options: list[Any] = [joinedload(Query.terms)]
    ) -> Query | None:
        session = self._get_session()

        return session.scalars(
            select(Query).options(*query_options).where(Query.id == id)
        ).first()

    def find_by_status(
        self, status: str, query_options: list[Any] = [joinedload(Query.terms)]
    ) -> list[Query]:
        session = self._get_session()

        return list(
            session.scalars(
                select(Query).options(*query_options).where(Query.status == status)
            ).unique()
        )

    def find_by_platform(
        self, platform: str, query_options: list[Any] = [joinedload(Query.terms)]
    ) -> list[Query]:
        session = self._get_session()

        return list(
            session.scalars(
                select(Query).options(*query_options).where(Query.platform == platform)
            ).unique()
        )

    def batch_delete(self, ids: list[UUID]) -> None:
        session = self._get_session()

        session.execute(delete(Query).where(Query.id.in_(ids)))
        session.commit()

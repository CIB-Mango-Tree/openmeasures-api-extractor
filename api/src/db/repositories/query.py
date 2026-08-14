from sqlalchemy import select, delete
from sqlalchemy.orm import Session, scoped_session, selectinload
from uuid import UUID
from .base import BaseRepository
from ..models import Query, QueryTerm, QueryRequest
from ...utils.constants import FETCH_INCOMPLETE, CLEAN_INCOMPLETE, PARSE_INCOMPLETE
from typing import Any

INCOMPLETE_STATUSES: list[str] = [FETCH_INCOMPLETE, CLEAN_INCOMPLETE, PARSE_INCOMPLETE]


class QueryRepository(BaseRepository[Query]):
    def __init__(self, factory: scoped_session[Session]) -> None:
        super().__init__(factory, Query)

    def find_all(
        self, query_options: list[Any] = [selectinload(Query.terms)]
    ) -> list[Query]:
        session: Session = self._session_factory()

        try:
            return list(
                session.scalars(
                    select(Query)
                    .options(*query_options)
                    .order_by(Query.created_at.desc())
                )
            )

        finally:
            session.close()
            self._session_factory.remove()

    def find_by_id(
        self, id: UUID, query_options: list[Any] = [selectinload(Query.terms)]
    ) -> Query | None:
        session: Session = self._session_factory()

        try:
            return session.scalars(
                select(Query)
                .options(*query_options)
                .where(Query.id == id)
            ).first()

        finally:
            session.close()
            self._session_factory.remove()

    def find_by_status(
        self, status: str, query_options: list[Any] = [selectinload(Query.terms)]
    ) -> list[Query]:
        session: Session = self._session_factory()

        try:
            return list(
                session.scalars(
                    select(Query)
                    .options(*query_options)
                    .where(Query.status == status)
                    .order_by(Query.created_at.desc())
                )
            )

        finally:
            session.close()
            self._session_factory.remove()

    def find_by_platform(
        self, platform: str, query_options: list[Any] = [selectinload(Query.terms)]
    ) -> list[Query]:
        session: Session = self._session_factory()

        try:
            return list(
                session.scalars(
                    select(Query)
                    .options(*query_options)
                    .where(Query.platform == platform)
                    .order_by(Query.created_at.desc())
                )
            )

        finally:
            session.close()
            self._session_factory.remove()

    def find_processed_data(self, id: UUID) -> bytes | None:
        """Reads the deferred blob as a single scalar, without materializing the ORM object."""
        session: Session = self._session_factory()

        try:
            return session.scalar(
                select(Query.processed_data).where(Query.id == id)
            )

        finally:
            session.close()
            self._session_factory.remove()

    def delete(self, id: UUID) -> None:
        self.batch_delete([id])

    def batch_delete(self, ids: list[UUID]) -> None:
        if len(ids) == 0:
            return

        session: Session = self._session_factory()

        try:
            # Children are removed explicitly: these are bulk DELETEs, which bypass the ORM-level
            # cascade="all, delete", and the schema has no ON DELETE CASCADE. Without this the
            # delete fails outright once PRAGMA foreign_keys=ON is enabled (and silently orphaned
            # terms and requests before it was).
            session.execute(delete(QueryTerm).where(QueryTerm.query_id.in_(ids)))
            session.execute(delete(QueryRequest).where(QueryRequest.query_id.in_(ids)))
            session.execute(delete(Query).where(Query.id.in_(ids)))
            session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()
            self._session_factory.remove()

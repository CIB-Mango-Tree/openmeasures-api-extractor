from sqlalchemy import select, delete
from sqlalchemy.orm import Session, scoped_session, joinedload
from uuid import UUID
from .base import BaseRepository
from ..models import Query
from ...utils.constants import FETCH_INCOMPLETE, CLEAN_INCOMPLETE, PARSE_INCOMPLETE


class QueryRepository(BaseRepository[Query]):
    def __init__(self, factory: scoped_session[Session]) -> None:
        super().__init__(factory, Query)

    def find_all(self, incomplete_only: bool = False) -> list[Query]:
        session = self._get_session()

        if incomplete_only:
            return list(
                session.scalars(
                    select(Query)
                    .options(joinedload(Query.terms), joinedload(Query.requests))
                    .where(
                        Query.status.in_(
                            [FETCH_INCOMPLETE, CLEAN_INCOMPLETE, PARSE_INCOMPLETE]
                        )
                    )
                ).all()
            )

        return list(
            session.scalars(
                select(Query).options(
                    joinedload(Query.terms), joinedload(Query.requests)
                )
            ).all()
        )

    def find_by_id(self, id: UUID) -> Query | None:
        session = self._get_session()

        return session.scalars(
            select(Query)
            .options(joinedload(Query.terms), joinedload(Query.requests))
            .where(Query.id == id)
        ).first()

    def find_by_status(self, status: str) -> list[Query]:
        session = self._get_session()

        return list(
            session.scalars(
                select(Query)
                .options(joinedload(Query.terms), joinedload(Query.requests))
                .where(Query.status == status)
            ).all()
        )

    def find_by_platform(
        self, platform: str, incomplete_only: bool = False
    ) -> list[Query]:
        session = self._get_session()

        if incomplete_only:
            return list(
                session.scalars(
                    select(Query)
                    .options(joinedload(Query.terms), joinedload(Query.requests))
                    .where(
                        Query.platform == platform,
                        Query.status.in_(
                            [FETCH_INCOMPLETE, CLEAN_INCOMPLETE, PARSE_INCOMPLETE]
                        ),
                    )
                ).all()
            )

        return list(
            session.scalars(
                select(Query)
                .options(joinedload(Query.terms), joinedload(Query.requests))
                .where(Query.platform == platform)
            ).all()
        )

    def batch_delete(self, ids: list[UUID]) -> None:
        session = self._get_session()

        session.execute(delete(Query).where(Query.id.in_(ids)))
        session.commit()

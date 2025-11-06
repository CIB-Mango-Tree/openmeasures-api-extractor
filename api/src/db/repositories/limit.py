from sqlalchemy import select, update as sql_update, delete as sql_delete
from sqlalchemy.orm import Session, scoped_session
from ..models import QueryLimit
from typing import Any


class QueryLimitRepository:
    _session_factory: scoped_session[Session]

    def __init__(self, factory: scoped_session[Session]) -> None:
        self._session_factory = factory

    def find(self) -> QueryLimit | None:
        session: Session = self._session_factory()

        return session.scalars(
            select(QueryLimit).execution_options(populate_existing=True)
        ).first()

    def create(self, model: QueryLimit) -> None:
        limit = self.find()

        if limit is not None:
            self.update(model)
            return

        session: Session = self._session_factory()

        session.add(model)
        session.commit()

    def update(self, model: QueryLimit) -> None:
        session: Session = self._session_factory()
        data: dict[str, Any] = {}

        for column in model.__table__.columns:
            name = column.name

            if hasattr(model, name):
                data[name] = getattr(model, name)

        session.execute(sql_update(QueryLimit).values(data))
        session.commit()

    def delete(self) -> None:
        session: Session = self._session_factory()

        session.execute(sql_delete(QueryLimit))
        session.commit()

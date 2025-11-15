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

        try:
            return session.scalars(
                select(QueryLimit).execution_options(populate_existing=True)
            ).first()

        finally:
            session.close()
            self._session_factory.remove()

    def create(self, model: QueryLimit) -> QueryLimit:
        limit = self.find()

        if limit is not None:
            return self.update(model)

        session: Session = self._session_factory()

        try:
            session.add(model)
            session.commit()
            session.refresh(model)
            session.expunge(model)

            return model

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()
            self._session_factory.remove()

    def update(self, model: QueryLimit) -> QueryLimit:
        session: Session = self._session_factory()

        try:
            model = session.merge(model)

            session.commit()
            session.refresh(model)
            session.expunge(model)

            return model

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()
            self._session_factory.remove()

    def delete(self) -> None:
        session: Session = self._session_factory()

        try:
            session.execute(sql_delete(QueryLimit))
            session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()
            self._session_factory.remove()

from sqlalchemy import delete as sql_delete, exists as sql_exists, select
from sqlalchemy.orm import Session, scoped_session
from uuid import UUID
from ..models.base import BaseModel
from typing import TypeVar, Any, cast

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository[ModelType]:
    _model: type[ModelType]
    _session_factory: scoped_session[Session]

    def __init__(
        self, factory: scoped_session[Session], model: type[ModelType]
    ) -> None:
        self._session_factory = factory
        self._model = model

    def create(self, model: ModelType) -> None:
        session: Session = self._session_factory()

        session.add(model)
        session.commit()

    def update(self, model: ModelType) -> None:
        session: Session = self._session_factory()

        session.merge(model)
        session.commit()

    def delete(self, id: UUID) -> None:
        model = cast(Any, self._model)
        session: Session = self._session_factory()

        session.execute(sql_delete(model).where(model.id == id))
        session.commit()

    def exists(self, id: UUID) -> bool:
        model = cast(Any, self._model)
        session: Session = self._session_factory()

        return (
            session.scalar(
                select(sql_exists(model).where(model.id == id)).execution_options(
                    populate_existing=True
                )
            )
            or False
        )

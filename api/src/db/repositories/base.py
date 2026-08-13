from sqlalchemy import (
    delete as sql_delete,
    exists as sql_exists,
    inspect,
    update as sql_update,
    select,
)
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

    def create(self, model: ModelType) -> ModelType:
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

    def update(self, model: ModelType, skip_relationships: bool = False) -> ModelType:
        session: Session = self._session_factory()

        try:
            if skip_relationships:
                model_any = cast(Any, model)
                model_class = type(model)
                model_class_any = cast(Any, model_class)
                pk_columns = model_any.__mapper__.primary_key
                pk_name = pk_columns[0].name
                pk_value = getattr(model, pk_name)
                update_data: dict[str, Any] = {}
                # Deferred columns that were never loaded would raise DetachedInstanceError here
                # (repositories close the session before returning). Skipping them also avoids
                # rewriting a multi-MB blob on every pagination update.
                unloaded = inspect(model).unloaded

                for column in model_any.__table__.columns:
                    if column.name == pk_name or column.key in unloaded:
                        continue

                    update_data[column.name] = getattr(model, column.name)

                if len(update_data) == 0:
                    return model

                session.execute(
                    sql_update(model_class)
                    .where(getattr(model_class_any, pk_name) == pk_value)
                    .values(update_data)
                )
                session.commit()

                return model

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

    def delete(self, id: UUID) -> None:
        model = cast(Any, self._model)
        session: Session = self._session_factory()

        try:
            session.execute(sql_delete(model).where(model.id == id))
            session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()
            self._session_factory.remove()

    def exists(self, id: UUID) -> bool:
        model = cast(Any, self._model)
        session: Session = self._session_factory()

        try:
            return (
                session.scalar(select(sql_exists(model).where(model.id == id))) or False
            )

        finally:
            session.close()
            self._session_factory.remove()

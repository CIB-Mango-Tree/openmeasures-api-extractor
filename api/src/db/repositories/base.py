from sqlalchemy import delete as sql_delete, exists as sql_exists, select
from sqlalchemy.orm import Session
from uuid import UUID
from ..models.base import BaseModel
from typing import TypeVar, Any, cast

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository[ModelType]:
    _model: type[ModelType]
    _db: Session

    def __init__(self, db: Session, model: type[ModelType]) -> None:
        self._db = db
        self._model = model

    def create(self, model: ModelType) -> None:
        self._db.add(model)
        self._db.commit()

    def update(self, model: ModelType) -> None:
        self._db.merge(model)
        self._db.commit()

    def delete(self, id: UUID) -> None:
        model = cast(Any, self._model)

        self._db.execute(sql_delete(model).where(model.id == id))
        self._db.commit()

    def exists(self, id: UUID) -> bool:
        model = cast(Any, self._model)
        entry_exists_query = self._db.scalar(
            select(sql_exists(model).where(model.id == id))
        )

        return entry_exists_query if entry_exists_query is not None else False

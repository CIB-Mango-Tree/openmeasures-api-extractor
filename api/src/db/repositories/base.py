from sqlalchemy import delete as sql_delete, select
from sqlalchemy.orm import Session
from ..models.base import Base, BaseWithTimestamp
from typing import TypeVar

ModelType = TypeVar("ModelType", Base, BaseWithTimestamp)


class BaseRepository[ModelType]:
    _model = ModelType
    _db: Session = None

    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, model: ModelType) -> None:
        self._db.add(model)
        self._db.commit()

    def update(self, model: ModelType) -> None:
        self._db.merge(model)
        self._db.commit()

    def delete(self, id: str) -> None:
        self._db.execute(sql_delete(self._model).where(self._model.id == id))
        self._db.commit()

    def exists(self, id: str) -> bool:
        return (
            self._db.execute(
                select(self._model).where(self._model.id == id).exists()
            ).scalar()
            is None
        )

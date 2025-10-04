from ..models import QueryLimit
from sqlalchemy import select, update as sql_update, delete as sql_delete
from sqlalchemy.orm import Session
from typing import Any


class QueryLimitRepository:
    _db: Session

    def __init__(self, db: Session) -> None:
        self._db = db

    def find(self) -> QueryLimit | None:
        return self._db.scalars(select(QueryLimit)).first()

    def create(self, model: QueryLimit) -> None:
        limit = self.find()

        if limit is not None:
            self.update(model)
            return

        self._db.add(model)
        self._db.commit()

    def update(self, model: QueryLimit) -> None:
        data: dict[str, Any] = {}

        for column in model.__table__.columns():
            if hasattr(model, column):
                data[column] = getattr(model, column)

        self._db.execute(sql_update(QueryLimit).values(data))
        self._db.commit()

    def delete(self) -> None:
        self._db.execute(sql_delete(QueryLimit))
        self._db.commit()

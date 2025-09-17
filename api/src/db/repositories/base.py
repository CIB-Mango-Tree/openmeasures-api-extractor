from sqlalchemy.orm import Session


class BaseRepository:
    _db: Session = None

    def __init__(self, db: Session) -> None:
        self._db = db

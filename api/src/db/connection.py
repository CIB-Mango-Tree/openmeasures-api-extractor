from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from .models.base import Base


def init_DB(url: str) -> scoped_session[Session]:
    engine = create_engine(
        url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

    Base.metadata.create_all(engine)

    return scoped_session(sessionmaker(engine))

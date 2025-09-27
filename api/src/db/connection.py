from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models.base import Base


def init_DB(url: str) -> Session:
    engine = create_engine(url)

    Base.metadata.create_all(engine)

    return sessionmaker(engine)

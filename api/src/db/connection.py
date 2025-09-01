from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


def init_DB(url: str) -> Session:
    engine = create_engine(url)

    return sessionmaker(engine)

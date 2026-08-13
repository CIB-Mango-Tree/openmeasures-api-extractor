from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlite3 import Connection as SQLiteConnection
from typing import Any
from .migrate import run_migrations, enable_wal, log_orphans

# SQLite serializes writes regardless of how many connections exist, so a large pool only deepens
# lock contention. The extraction pipeline runs repository calls on worker threads via to_thread,
# and scoped_session gives each of those its own connection.
POOL_SIZE = 5
MAX_OVERFLOW = 5

# Long enough to ride out a slow write from the extraction pipeline instead of failing with
# "database is locked" immediately.
BUSY_TIMEOUT_MS = 30_000


@event.listens_for(Engine, "connect")
def _set_sqlite_pragmas(dbapi_connection: Any, _: Any) -> None:
    if not isinstance(dbapi_connection, SQLiteConnection):
        return

    cursor = dbapi_connection.cursor()

    try:
        # Off by default in SQLite, which is why the schema's foreign keys have never actually
        # been enforced. Deletes clean up children explicitly to stay compatible with this.
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
        # Safe under WAL: survives application crashes, and can only lose the last transaction
        # on a full OS crash.
        cursor.execute("PRAGMA synchronous=NORMAL")

    finally:
        cursor.close()


def init_DB(url: str) -> scoped_session[Session]:
    is_sqlite = url.startswith("sqlite")
    engine = create_engine(
        url,
        pool_pre_ping=True,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        # Repository calls run on to_thread workers, so connections cross thread boundaries.
        connect_args={"check_same_thread": False} if is_sqlite else {},
    )

    if is_sqlite:
        enable_wal(engine)

    # Alembic owns the schema now; create_all is deliberately gone. It skipped existing tables
    # wholesale, which is why an installed database could never receive a new index.
    run_migrations(engine)

    if is_sqlite:
        log_orphans(engine)

    return scoped_session(sessionmaker(engine, autoflush=False))

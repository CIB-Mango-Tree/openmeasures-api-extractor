from alembic import command
from alembic.config import Config
from pathlib import Path
from sqlalchemy import Engine
import sys
from ..log import logger


def _script_location() -> Path:
    """Resolves the alembic directory both from source and inside the PyInstaller bundle."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")) / "alembic"

    # api/src/db/migrate.py -> api/alembic
    return Path(__file__).resolve().parents[2] / "alembic"


def _config() -> Config:
    config = Config()

    config.set_main_option("script_location", str(_script_location()))
    # Silences alembic's own logging config; the app configures logging in src/log.py.
    config.set_main_option("sqlalchemy.url", "")

    return config


def run_migrations(engine: Engine) -> None:
    """Brings the database to head. Safe from any starting state, including a pre-Alembic
    database created by create_all() -- revision 0001 adopts an existing schema rather than
    recreating it, so no stamping step is needed."""
    config = _config()

    # Alembic runs against the application's own connection (see alembic/env.py) so migrations
    # share the engine and its PRAGMAs rather than opening a second one.
    with engine.connect() as connection:
        config.attributes["connection"] = connection

        command.upgrade(config, "head")

    logger.info("database schema is up to date")


def log_orphans(engine: Engine) -> None:
    """Enabling foreign_keys=ON does not validate existing rows, so report pre-existing orphans."""
    with engine.connect() as connection:
        orphans = connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall()

    if orphans:
        logger.warning(
            "database contains %d orphaned row(s) predating foreign key enforcement",
            len(orphans),
        )


def enable_wal(engine: Engine) -> None:
    """journal_mode is persisted in the file itself, so it is set once rather than per connect."""
    with engine.connect() as connection:
        mode = connection.exec_driver_sql("PRAGMA journal_mode=WAL").scalar()

    if str(mode).lower() != "wal":
        logger.warning("could not enable WAL journal mode (currently %s)", mode)

"""move extracted posts out of the database into Parquet files

Post data was stored three times: requests.data (raw hits), requests.cleaned_data (a near
duplicate) and queries.processed_data (a Feather blob). On a real install that was 747 MB of
database holding 56 rows, and every list query dragged the blobs through SQLite.

This migration writes the payloads out to <app_data_dir>/datasets/<query_id>/ and then drops the
columns. It is re-runnable: files already written are skipped, and the column drop only happens
once the data has been moved.

Note that space is not reclaimed until the database is VACUUMed, which this deliberately does not
do -- VACUUM needs an exclusive lock and roughly twice the file size in free space.

Revision ID: 0003
Revises: 0002
"""

from io import BytesIO
from json import loads
from typing import Any, Sequence, Union
from uuid import UUID

import polars as pl
import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _log(message: str) -> None:
    # Imported lazily so the migration still loads if logging configuration changes.
    from src.log import logger

    logger.info("migration 0003: %s", message)


def _migrate_raw_pages(connection: sa.Connection) -> None:
    from src.storage.dataset import extract_hits, raw_page_path, write_raw_page

    rows = connection.execute(
        sa.text(
            "SELECT r.id, r.query_id, q.platform "
            "FROM requests r JOIN queries q ON q.id = r.query_id "
            "WHERE r.data IS NOT NULL"
        )
    ).fetchall()

    _log(f"moving {len(rows)} request pages to Parquet")

    for request_id, query_id, platform in rows:
        request_uuid = UUID(str(request_id))
        query_uuid = UUID(str(query_id))

        if raw_page_path(query_uuid, request_uuid).exists():
            continue

        payload = connection.execute(
            sa.text("SELECT data FROM requests WHERE id = :id"), {"id": request_id}
        ).scalar()

        if not payload:
            continue

        hits: list[dict[str, Any]] = loads(payload)

        write_raw_page(query_uuid, request_uuid, extract_hits(platform, hits))


def _migrate_processed(connection: sa.Connection) -> None:
    from src.storage.dataset import processed_path, write_processed

    rows = connection.execute(
        sa.text("SELECT id FROM queries WHERE processed_data IS NOT NULL")
    ).fetchall()

    _log(f"moving {len(rows)} processed datasets to Parquet")

    for (query_id,) in rows:
        query_uuid = UUID(str(query_id))

        if processed_path(query_uuid).exists():
            continue

        blob = connection.execute(
            sa.text("SELECT processed_data FROM queries WHERE id = :id"),
            {"id": query_id},
        ).scalar()

        if not blob:
            continue

        # The blobs are Feather V2, which is Arrow IPC -- polars reads them directly.
        write_processed(query_uuid, pl.read_ipc(BytesIO(blob)))


def _drop_column(connection: sa.Connection, table: str, column: str) -> None:
    """Drops a column in place.

    Deliberately not op.batch_alter_table: on SQLite that rebuilds the table by dropping and
    recreating it, which fails against `queries` because terms and requests hold foreign keys to
    it and enforcement is now on. Native ALTER TABLE ... DROP COLUMN (SQLite 3.35+) touches only
    the one column and leaves the foreign keys intact.
    """
    columns = {row[1] for row in connection.execute(sa.text(f"PRAGMA table_info({table})"))}

    if column not in columns:
        return

    connection.execute(sa.text(f'ALTER TABLE {table} DROP COLUMN "{column}"'))


def upgrade() -> None:
    connection = op.get_bind()

    version = tuple(
        int(part) for part in str(connection.exec_driver_sql("SELECT sqlite_version()").scalar()).split(".")
    )

    if version < (3, 35, 0):
        raise RuntimeError(
            f"SQLite 3.35+ is required to drop the payload columns (found {version})"
        )

    _migrate_raw_pages(connection)
    _migrate_processed(connection)

    _drop_column(connection, "requests", "cleaned_data")
    _drop_column(connection, "requests", "data")
    _drop_column(connection, "queries", "processed_data")

    _log("payload columns dropped; run VACUUM to reclaim the space")


def downgrade() -> None:
    # The columns come back empty: the data now lives on disk and is not copied back.
    with op.batch_alter_table("queries") as batch:
        batch.add_column(sa.Column("processed_data", sa.LargeBinary(), nullable=True))

    with op.batch_alter_table("requests") as batch:
        batch.add_column(sa.Column("data", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("cleaned_data", sa.JSON(), nullable=True))

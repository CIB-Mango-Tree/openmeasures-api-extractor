"""baseline schema

This reproduces the schema that Base.metadata.create_all() produced before migrations existed.
Installs predating Alembic are stamped at this revision rather than running it, so it must match
what they already have on disk exactly -- in particular it carries no non-primary-key indexes.

Revision ID: 0001
Revises:
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Adopt an existing pre-Alembic schema rather than recreating it. Databases built by
    # create_all() already have these tables, and this keeps `upgrade head` valid from any
    # starting state -- for the application and the alembic CLI alike -- with no stamping step.
    if sa.inspect(op.get_bind()).has_table("queries"):
        return

    op.create_table(
        "queries",
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=True),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=False),
        sa.Column("platform", sa.String(length=64), nullable=False),
        sa.Column("current_timestamp", sa.DateTime(), nullable=True),
        sa.Column("queries_used", sa.Integer(), nullable=False),
        sa.Column("rows_fetched", sa.Integer(), nullable=False),
        sa.Column("percentage", sa.Float(), nullable=False),
        sa.Column("processed_data", sa.LargeBinary(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "limit",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("percentage", sa.Float(), nullable=False),
        sa.Column("previous_request_date", sa.DateTime(), nullable=True),
        sa.Column("limit_refresh_date", sa.DateTime(), nullable=True),
        sa.CheckConstraint("id = 1", name="singleton_check"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "terms",
        sa.Column("query_id", sa.Uuid(), nullable=False),
        sa.Column("modifier", sa.String(length=8), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("term", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["query_id"], ["queries.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "requests",
        sa.Column("query_id", sa.Uuid(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("cleaned_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["query_id"], ["queries.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("requests")
    op.drop_table("terms")
    op.drop_table("limit")
    op.drop_table("queries")

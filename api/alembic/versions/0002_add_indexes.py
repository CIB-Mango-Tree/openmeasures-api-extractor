"""add the missing foreign key and lookup indexes

None of these existed before: EXPLAIN QUERY PLAN showed SQLite building an AUTOMATIC COVERING
INDEX on terms.query_id for every list request. Names follow SQLAlchemy's ix_<table>_<column>
convention so a migrated database matches a freshly created one.

Revision ID: 0002
Revises: 0001
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_terms_query_id", "terms", ["query_id"])
    op.create_index("ix_requests_query_id", "requests", ["query_id"])
    op.create_index("ix_queries_status", "queries", ["status"])
    op.create_index("ix_queries_platform", "queries", ["platform"])


def downgrade() -> None:
    op.drop_index("ix_queries_platform", table_name="queries")
    op.drop_index("ix_queries_status", table_name="queries")
    op.drop_index("ix_requests_query_id", table_name="requests")
    op.drop_index("ix_terms_query_id", table_name="terms")

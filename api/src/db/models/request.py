from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID
from .base import BaseModelWithTimestamp


class QueryRequest(BaseModelWithTimestamp):
    """A single fetched page. The hits themselves live in a Parquet file named after this row's
    id (see src/storage/dataset.py); only the metadata is kept here."""

    __tablename__: str = "requests"
    query_id: Mapped[UUID] = mapped_column(
        ForeignKey("queries.id"), nullable=False, index=True
    )
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)

from sqlalchemy import JSON, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID
from .base import BaseModelWithTimestamp
from typing import Any


class QueryRequest(BaseModelWithTimestamp):
    __tablename__: str = "requests"
    query_id: Mapped[UUID] = mapped_column(ForeignKey("queries.id"), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    cleaned_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

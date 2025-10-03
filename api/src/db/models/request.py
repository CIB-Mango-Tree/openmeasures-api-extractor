from .base import BaseModelWithTimestamp
from sqlalchemy import UUID, INTEGER, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class QueryRequest(BaseModelWithTimestamp):
    __tablename__ = "requests"
    query_id: Mapped[UUID] = mapped_column(
        ForeignKey("queries.id"), nullable=False)
    row_count: Mapped[INTEGER] = mapped_column(INTEGER, nullable=False)
    data: Mapped[JSON] = mapped_column(JSON, nullable=False)
    cleaned_data: Mapped[JSON] = mapped_column(JSON, nullable=True)

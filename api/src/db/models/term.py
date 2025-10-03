from .base import BaseModel
from sqlalchemy import VARCHAR, TEXT, UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class QueryTerm(BaseModel):
    __tablename__ = "terms"
    query_id: Mapped[UUID] = mapped_column(
        ForeignKey("queries.id"), nullable=False)
    modifier: Mapped[VARCHAR] = mapped_column(
        VARCHAR(8), nullable=False, default="EQUAL"
    )
    term: Mapped[TEXT] = mapped_column(TEXT, nullable=False)

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID
from .base import BaseModel


class QueryTerm(BaseModel):
    __tablename__: str = "terms"
    query_id: Mapped[UUID] = mapped_column(ForeignKey("queries.id"), nullable=False)
    modifier: Mapped[str] = mapped_column(String(8), nullable=False, default="EQUAL")
    term: Mapped[str] = mapped_column(Text, nullable=False)

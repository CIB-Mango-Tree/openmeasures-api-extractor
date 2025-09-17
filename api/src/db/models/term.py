from .base import Base
from sqlalchemy import VARCHAR, TEXT, UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class QueryTerm(Base):
    query_ID: Mapped[UUID] = mapped_column(ForeignKey("query.id"), nullable=False)
    modifier: Mapped[VARCHAR] = mapped_column(
        VARCHAR(8), nullable=False, default="EQUAL"
    )
    term: Mapped[TEXT] = mapped_column(TEXT, nullable=False)

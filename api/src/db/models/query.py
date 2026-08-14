from sqlalchemy import DateTime, String, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from .base import BaseModelWithTimestamp
from .term import QueryTerm
from .request import QueryRequest
from ...utils.constants import FETCH_IN_PROGRESS
from ...utils.search import quote_term


class Query(BaseModelWithTimestamp):
    __tablename__: str = "queries"
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=FETCH_IN_PROGRESS, index=True
    )
    timezone: Mapped[str] = mapped_column(String(64), nullable=True)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    platform: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    current_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    queries_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_fetched: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    terms: Mapped[list[QueryTerm]] = relationship(
        cascade="all, delete", order_by="QueryTerm.position"
    )
    requests: Mapped[list[QueryRequest]] = relationship(cascade="all, delete")

    def increment_queries_used(self, step: int = 1) -> None:
        if step <= 0:
            return

        self.queries_used += step


    @property
    def term(self) -> str:
        if len(self.terms) == 0:
            return ""

        output: str = ""

        for term in self.terms:
            value = quote_term(term.term)
            output += f" {term.modifier} {value}" if len(output) > 0 else value

        return output

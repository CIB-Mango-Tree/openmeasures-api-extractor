from .base import BaseWithTimestamp
from .term import QueryTerm
from .request import QueryRequest
from sqlalchemy import DateTime, VARCHAR, INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List


class Query(BaseWithTimestamp):
    status: Mapped[VARCHAR] = mapped_column(
        VARCHAR(16), nullable=False, default="IN_PROGRESS"
    )
    timezone: Mapped[VARCHAR] = mapped_column(VARCHAR(64), nullable=True)
    start_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    platform: Mapped[VARCHAR] = mapped_column(VARCHAR(64), nullable=False)
    row_count: Mapped[INTEGER] = mapped_column(INTEGER, nullable=False)
    rows_fetched: Mapped[INTEGER] = mapped_column(INTEGER, nullable=False)
    terms: Mapped[List[QueryTerm]] = relationship()
    requests: Mapped[List[QueryRequest]] = relationship()

    @property
    def progress(self):
        return (self.rows_fetched / self.row_count) * 100

from .base import BaseWithTimestamp
from .term import QueryTerm
from .request import QueryRequest
from sqlalchemy import DateTime, VARCHAR, INTEGER, FLOAT, VARBINARY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List


class Query(BaseWithTimestamp):
    status: Mapped[VARCHAR] = mapped_column(
        VARCHAR(16), nullable=False, default="FETCH:IN_PROGRESS"
    )
    timezone: Mapped[VARCHAR] = mapped_column(VARCHAR(64), nullable=True)
    start_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    platform: Mapped[VARCHAR] = mapped_column(VARCHAR(64), nullable=False)
    rows_fetched: Mapped[INTEGER] = mapped_column(
        INTEGER, nullable=False, default=0)
    percentage: Mapped[FLOAT] = mapped_column(FLOAT, nullable=False, default=0)
    processed_data: Mapped[VARBINARY] = mapped_column(VARBINARY, nullable=True)
    terms: Mapped[List[QueryTerm]] = relationship()
    requests: Mapped[List[QueryRequest]] = relationship()

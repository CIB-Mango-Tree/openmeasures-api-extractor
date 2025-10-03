from .base import BaseModelWithTimestamp
from .term import QueryTerm
from .request import QueryRequest
from ...utils.constants import EQ, FETCH_IN_PROGRESS
from sqlalchemy import DateTime, VARCHAR, INTEGER, FLOAT, VARBINARY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pandas import DataFrame, json_normalize, read_feather
from io import BytesIO
from typing import List


class Query(BaseModelWithTimestamp):
    __tablename__ = "queries"
    status: Mapped[VARCHAR] = mapped_column(
        VARCHAR(16), nullable=False, default=FETCH_IN_PROGRESS
    )
    timezone: Mapped[VARCHAR] = mapped_column(VARCHAR(64), nullable=True)
    start_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    platform: Mapped[VARCHAR] = mapped_column(VARCHAR(64), nullable=False)
    current_timestamp: Mapped[DateTime] = mapped_column(
        DateTime, nullable=True)
    rows_fetched: Mapped[INTEGER] = mapped_column(
        INTEGER, nullable=False, default=0)
    percentage: Mapped[FLOAT] = mapped_column(FLOAT, nullable=False, default=0)
    processed_data: Mapped[VARBINARY] = mapped_column(VARBINARY, nullable=True)
    terms: Mapped[List[QueryTerm]] = relationship(cascade="all, delete")
    requests: Mapped[List[QueryRequest]] = relationship(cascade="all, delete")

    def from_requests_to_dataframe(self) -> DataFrame:
        return json_normalize([request.cleaned_data for request in self.requests])

    def from_dataframe_to_processed_data(self, data_frame: DataFrame) -> None:
        buffer = BytesIO()

        data_frame.to_feather(buffer)
        self.processed_data = buffer.getvalue()

    def from_processed_data_to_dataframe(self) -> DataFrame:
        buffer = BytesIO()
        buffer.write(self.processed_data)

        return read_feather(buffer)

    @property
    def term(self) -> str:
        if len(self.terms) == 0:
            return ""

        base = next(
            (term.term for term in self.terms if term.modifier == EQ), None)

        if base is None:
            return ""

        output = base

        for term in self.terms:
            if term.modifier != EQ:
                output += f" {term.modifier} {term.term}"

        return output

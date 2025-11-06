from sqlalchemy import DateTime, String, Integer, Float, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pandas import DataFrame, json_normalize, read_feather
from io import BytesIO
from sys import getsizeof
from datetime import datetime
from .base import BaseModelWithTimestamp
from .term import QueryTerm
from .request import QueryRequest
from ...utils.constants import FETCH_IN_PROGRESS


class Query(BaseModelWithTimestamp):
    __tablename__: str = "queries"
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=FETCH_IN_PROGRESS
    )
    timezone: Mapped[str] = mapped_column(String(64), nullable=True)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    current_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    queries_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_fetched: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    processed_data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    terms: Mapped[list[QueryTerm]] = relationship(
        cascade="all, delete", order_by="QueryTerm.position"
    )
    requests: Mapped[list[QueryRequest]] = relationship(cascade="all, delete")

    def increment_queries_used(self, step: int = 1) -> None:
        if step <= 0:
            return

        self.queries_used += step

    def from_requests_to_dataframe(self) -> DataFrame:
        data = []

        for request in self.requests:
            if request.cleaned_data is not None:
                data.extend(request.cleaned_data)

        return json_normalize(data)

    def from_dataframe_to_processed_data(self, data_frame: DataFrame) -> None:
        buffer = BytesIO()

        data_frame.to_feather(buffer)
        self.processed_data = buffer.getvalue()

    def from_processed_data_to_dataframe(self) -> DataFrame | None:
        if self.processed_data is None:
            return None

        if getsizeof(self.processed_data) == 0:
            return None

        buffer = BytesIO()
        buffer.write(self.processed_data)

        return read_feather(buffer)

    @property
    def term(self) -> str:
        if len(self.terms) == 0:
            return ""

        output: str = ""

        for term in self.terms:
            output += f" {term.modifier} {term.term}" if len(output) > 0 else term.term

        return output

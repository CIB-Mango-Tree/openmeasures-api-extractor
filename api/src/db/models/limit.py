from sqlalchemy import INTEGER, DateTime, FLOAT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class QueryLimit(DeclarativeBase):
    count: Mapped[INTEGER] = mapped_column(INTEGER, nullable=False, default=39)
    percentage: Mapped[FLOAT] = mapped_column(FLOAT, nullable=False, default=0)
    previous_request_date: Mapped[DateTime] = mapped_column(
        DateTime, nullable=True)
    limit_refresh_date: Mapped[DateTime] = mapped_column(
        DateTime, nullable=True)

    def decrement(self) -> None:
        if self.count == 0:
            return

        self.count -= 1

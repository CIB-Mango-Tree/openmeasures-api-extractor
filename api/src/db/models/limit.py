from sqlalchemy import INTEGER, DateTime, FLOAT, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base
from datetime import datetime, timedelta


class QueryLimit(Base):
    __tablename__ = "limit"
    id: Mapped[INTEGER] = mapped_column(
        INTEGER, primary_key=True, nullable=False, default=1
    )
    count: Mapped[INTEGER] = mapped_column(INTEGER, nullable=False, default=39)
    percentage: Mapped[FLOAT] = mapped_column(FLOAT, nullable=False, default=0)
    previous_request_date: Mapped[DateTime] = mapped_column(
        DateTime, nullable=True)
    limit_refresh_date: Mapped[DateTime] = mapped_column(
        DateTime, nullable=True)
    __table_args__ = (CheckConstraint(id == 1, name="singleton_check"),)

    def decrement(self) -> None:
        if self.count == 0:
            return

        self.count -= 1

    def set_timestamps(self) -> None:
        now = datetime.now()
        self.previous_request_date = now
        self.limit_refresh_date = now + timedelta(days=1)

    def set_percentage(self) -> None:
        self.percentage = self.count / 39

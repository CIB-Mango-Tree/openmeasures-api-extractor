from sqlalchemy import DateTime, Integer, Float, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base
from datetime import datetime, timedelta


class QueryLimit(Base):
    __tablename__: str = "limit"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, nullable=False, default=1
    )
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=39)
    percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    previous_request_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    limit_refresh_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    __table_args__: tuple[CheckConstraint] = (
        CheckConstraint(id == 1, name="singleton_check"),
    )

    def decrement(self, step: int = 1) -> None:
        if self.count == 0:
            return

        if step < 0 or (self.count - step) < 0:
            return

        self.count -= step

    def set_timestamps(self) -> None:
        now = datetime.now()
        self.previous_request_date = now
        self.limit_refresh_date = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0
        )

    def set_percentage(self) -> None:
        self.percentage = self.count / 39

    def reset(self) -> None:
        self.count = 39
        self.percentage = 0
        self.limit_refresh_date = None

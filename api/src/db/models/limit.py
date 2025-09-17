from sqlalchemy import INTEGER, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class QueryLimit(DeclarativeBase):
    count: Mapped[INTEGER] = mapped_column(INTEGER, nullable=False, default=39)
    previous_request_date: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    limit_refresh_date: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

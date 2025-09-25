from sqlalchemy import UUID, DateTime
from uuid import uuid4
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime


class Base(DeclarativeBase):
    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid4())


class BaseWithTimestamp(Base):
    created_at: Mapped[DateTime] = mapped_column(
        DateTime, nullable=False, default=datetime.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    def set_updated_at(self) -> None:
        self.updated_at = datetime.now()

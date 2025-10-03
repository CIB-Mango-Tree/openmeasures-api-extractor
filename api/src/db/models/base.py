from sqlalchemy import UUID, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base
from uuid import uuid4
from datetime import datetime

Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True
    id: Mapped[UUID] = mapped_column(
        UUID, primary_key=True, nullable=False, default=uuid4()
    )


class BaseModelWithTimestamp(BaseModel):
    __abstract__ = True
    created_at: Mapped[DateTime] = mapped_column(
        DateTime, nullable=False, default=datetime.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    def set_updated_at(self) -> None:
        self.updated_at = datetime.now()

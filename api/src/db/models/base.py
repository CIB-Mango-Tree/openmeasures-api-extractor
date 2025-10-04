from sqlalchemy import UUID, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base
from uuid import uuid4, UUID as UUIDType
from datetime import datetime

Base = declarative_base()


class BaseModel(Base):
    __abstract__: bool = True
    id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid4
    )


class BaseModelWithTimestamp(BaseModel):
    __abstract__: bool = True
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def set_updated_at(self) -> None:
        self.updated_at = datetime.now()

from sqlalchemy import UUID
from uuid import uuid4
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid4())

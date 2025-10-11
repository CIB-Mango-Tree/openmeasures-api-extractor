from pydantic import BaseModel, Field, UUID4, ValidationInfo, field_validator
from pydantic_core import PydanticCustomError
from tzlocal import get_localzone_name
from .term import TermValidator
from ..log import logger
from datetime import datetime
from dateutil.relativedelta import relativedelta
from zoneinfo import ZoneInfo


class CreateQueryValidator(BaseModel):
    platform: str = Field(min_length=1)
    term: str = Field(min_length=1)
    term_modifiers: list[TermValidator] | None
    timezone: str | None = Field(default=get_localzone_name())
    end_date: datetime
    start_date: datetime

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, value: datetime) -> datetime:
        now = datetime.now()

        if value > (now - relativedelta(months=6)):
            raise PydanticCustomError(
                "datetime_past",
                "the end date must be at least 6 months in the past from today",
            )

        return value

    @field_validator("start_date", mode="after")
    @classmethod
    def validate_start_date(cls, value: datetime, info: ValidationInfo) -> datetime:
        now = datetime.now()

        if value > (now - relativedelta(months=6)):
            raise PydanticCustomError(
                "date_past",
                "the start date must be at least 6 months in the past from today",
            )

        if "end_date" not in info.data:
            return value

        if value > info.data["end_date"]:
            raise PydanticCustomError(
                "date_past", "the start date must not be greater than the end date"
            )

        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)

            return value

        except Exception:
            raise PydanticCustomError(
                "value_error", "a valid timezone must be provided"
            )


class UpdateQueryValidator(BaseModel):
    status: str = Field(min_length=1)


class DeleteQueriesValidator(BaseModel):
    ids: list[UUID4]

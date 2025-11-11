from pydantic import BaseModel, Field, UUID4, ValidationInfo, field_validator
from pydantic_core import PydanticCustomError
from tzlocal import get_localzone_name
from .term import TermValidator
from datetime import datetime
from dateutil.relativedelta import relativedelta
from zoneinfo import ZoneInfo
from ..utils.constants import EQ


class CreateQueryValidator(BaseModel):
    platform: str = Field(min_length=1)
    terms: list[TermValidator]
    timezone: str | None = Field(default=get_localzone_name())
    end_date: datetime
    start_date: datetime

    @field_validator("terms")
    @classmethod
    def validate_terms(cls, value: list[TermValidator]) -> list[TermValidator]:
        if len(value) == 0:
            raise PydanticCustomError(
                "value_error", "At least one term must be provided"
            )

        if value[0].modifier != EQ:
            raise PydanticCustomError(
                "value_error", "The modifier for the first term must be set to EQUAL"
            )

        return value

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, value: datetime, info: ValidationInfo) -> datetime:
        timezone: str = info.data.get("timezone", "")
        now = datetime.now().replace(tzinfo=ZoneInfo(timezone))

        if value.replace(tzinfo=ZoneInfo(timezone)) > (now - relativedelta(months=6)):
            raise PydanticCustomError(
                "datetime_past",
                "the end date must be at least 6 months in the past from today",
            )

        return value

    @field_validator("start_date", mode="after")
    @classmethod
    def validate_start_date(cls, value: datetime, info: ValidationInfo) -> datetime:
        timezone: str = info.data.get("timezone", "")
        now: datetime = datetime.now().replace(tzinfo=ZoneInfo(timezone))
        localized_value: datetime = value.replace(tzinfo=ZoneInfo(timezone))

        if localized_value > (now - relativedelta(months=6)):
            raise PydanticCustomError(
                "date_past",
                "the start date must be at least 6 months in the past from today",
            )

        if localized_value > info.data["end_date"].replace(tzinfo=ZoneInfo(timezone)):
            raise PydanticCustomError(
                "date_past", "the start date must not be greater than the end date"
            )

        return value

    @field_validator("timezone", mode="before")
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

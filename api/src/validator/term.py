from pydantic import BaseModel, Field
from enum import Enum
from ..utils.constants import EQ, AND, OR, NOT


class TermModifiers(Enum):
    EQUAL = EQ
    NOT = NOT
    AND = AND
    OR = OR


class TermValidator(BaseModel):
    modifier: TermModifiers
    term: str = Field(min_length=1)

from pydantic import BaseModel, Field


class TermValidator(BaseModel):
    modifier: str = Field(min_length=1)
    term: str = Field(min_length=1)

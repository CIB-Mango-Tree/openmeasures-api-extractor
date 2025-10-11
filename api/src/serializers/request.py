from pydantic import BaseModel, ConfigDict
from typing import Any


class QueryRequestSerializer(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    row_count: int
    data: list[dict[str, Any]] | None
    cleaned_data: list[dict[str, Any]] | None

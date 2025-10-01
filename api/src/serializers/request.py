from pydantic import BaseModel, ConfigDict
from typing import Dict, Any


class QueryRequestSerializer(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    row_count: int
    data: Dict[str, Any]
    cleaned_data: Dict[str, Any]

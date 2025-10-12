from .base import BaseSerializer
from typing import Any


class QueryRequestSerializer(BaseSerializer):
    row_count: int
    data: list[dict[str, Any]] | None
    cleaned_data: list[dict[str, Any]] | None

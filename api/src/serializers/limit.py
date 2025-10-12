from datetime import datetime
from .base import BaseSerializer


class QueryLimitSerializer(BaseSerializer):
    count: int
    percentage: float
    previous_request_date: datetime | None = None
    limit_refresh_date: datetime | None = None

from .base import BaseSerializer


class QueryTermSerializer(BaseSerializer):
    term: str
    modifier: str

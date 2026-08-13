from .base import BaseSerializer


class QueryRequestSerializer(BaseSerializer):
    # data/cleaned_data are gone: the hits live in Parquet on disk, and serializing them here
    # meant GET /api/queries?include_requests=true could return hundreds of megabytes.
    row_count: int

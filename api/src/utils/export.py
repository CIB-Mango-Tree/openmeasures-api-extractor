from pydantic import BaseModel


class FileExport(BaseModel):
    filename: str
    data: bytes
    # Carried here so the endpoint does not re-derive it: the format was branched on in both the
    # service and the endpoint, and the two mappings could drift apart.
    content_type: str

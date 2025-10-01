from pydantic import BaseModel, ConfigDict


class QueryTermSerializer(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    term: str
    modifier: str

from pydantic import BaseModel, UUID


class ParamValidator(BaseModel):
    id: UUID

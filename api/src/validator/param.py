from pydantic import BaseModel, UUID4


class ParamValidator(BaseModel):
    id: UUID4

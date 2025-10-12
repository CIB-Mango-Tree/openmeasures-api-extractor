from pydantic import BaseModel, ConfigDict
from ..db.models.base import BaseModel as ModelBase, BaseModelWithTimestamp
from typing import Any


class BaseSerializer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def convert_model_to_dict(cls, model: ModelBase) -> dict[str, Any]:
        return cls.model_validate(model).model_dump(mode="json")

    @classmethod
    def convert_models_to_dict(
        cls, models: list[ModelBase | BaseModelWithTimestamp]
    ) -> list[dict[str, Any]]:
        return [cls.model_validate(model).model_dump(mode="json") for model in models]

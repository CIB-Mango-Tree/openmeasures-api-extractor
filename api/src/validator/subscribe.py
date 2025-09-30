from pydantic import BaseModel, UUID
from enum import Enum
from ..utils.constants import SUBSCRIBE, UNSUBSCRIBE


class Actions(Enum):
    SUBSCRIBE = SUBSCRIBE
    UNSUBSCRIBE = UNSUBSCRIBE


class SubscriptionActionValidator(BaseModel):
    action: Actions
    topic: UUID

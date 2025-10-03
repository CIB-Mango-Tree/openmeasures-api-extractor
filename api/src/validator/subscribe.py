from pydantic import BaseModel, UUID4
from enum import Enum
from ..utils.constants import SUBSCRIBE, UNSUBSCRIBE


class Actions(Enum):
    SUBSCRIBE = SUBSCRIBE
    UNSUBSCRIBE = UNSUBSCRIBE


class SubscriptionActionValidator(BaseModel):
    action: Actions
    topic: UUID4

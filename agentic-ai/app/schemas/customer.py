from enum import Enum
from pydantic import BaseModel
from typing import Optional

class CustomerIntent(str, Enum):
    CONFIRM = "CONFIRM"
    MAYBE = "MAYBE"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    NO_RESPONSE = "NO_RESPONSE"
    UNKNOWN = "UNKNOWN"

class CustomerResponse(BaseModel):
    response_type: CustomerIntent
    confidence: float
    requested_time: Optional[str] = None
    customer_message: Optional[str] = None

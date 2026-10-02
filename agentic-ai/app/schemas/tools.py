from pydantic import BaseModel
from typing import Literal

class ToolMetadata(BaseModel):
    name: str
    operation: Literal["READ", "WRITE"]
    requires_confirmation: bool

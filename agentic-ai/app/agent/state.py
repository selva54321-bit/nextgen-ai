from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    session_id: str
    user_id: str
    messages: Annotated[Sequence[BaseMessage], operator.add]
    correlation_id: str
    errors: list[str]

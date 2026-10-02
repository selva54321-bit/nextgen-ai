from typing import TypedDict, Any

class AgentState(TypedDict, total=False):
    session_id: str
    user_id: str
    user_message: str
    intent: str
    context: dict[str, Any]
    selected_tool: str
    tool_input: dict[str, Any]
    tool_output: dict[str, Any]
    action_type: str
    action_allowed: bool
    confirmation_required: bool
    execution_result: dict[str, Any]
    response: str
    errors: list[str]
    correlation_id: str

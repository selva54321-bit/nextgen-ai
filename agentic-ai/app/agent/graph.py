from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .nodes import call_model
from langgraph.prebuilt import ToolNode
from ..tools.dispatch_tools import get_dispatch_queue, get_priority_orders
from ..tools.delivery_tools import get_delivery_risk
from ..tools.action_tools import update_order_priority


tools = [get_dispatch_queue, get_priority_orders, get_delivery_risk, update_order_priority]
tool_node = ToolNode(tools)

def should_continue(state: AgentState) -> str:
    messages = state.get("messages", [])
    if not messages:
        return END
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END

from langgraph.checkpoint.memory import MemorySaver

def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )
    workflow.add_edge("tools", "agent")
    
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)

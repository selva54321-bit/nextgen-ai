from .state import AgentState
from .llm_provider import get_llm
from ..tools.dispatch_tools import get_dispatch_queue, get_priority_orders
from ..tools.delivery_tools import get_delivery_risk
from ..tools.action_tools import update_order_priority
import logging
from langchain_core.messages import SystemMessage

logger = logging.getLogger(__name__)
tools = [get_dispatch_queue, get_priority_orders, get_delivery_risk, update_order_priority]

async def call_model(state: AgentState):
    logger.info("Calling LLM")
    llm = get_llm()
    llm_with_tools = llm.bind_tools(tools)
    
    messages = state.get("messages", [])
    if not any(isinstance(m, SystemMessage) for m in messages):
        sys_msg = SystemMessage(content="You are an autonomous logistics agent. You can fetch data from the database or backend, and perform actions. Always use the provided tools to answer queries.")
        messages = [sys_msg] + messages
        
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response]}

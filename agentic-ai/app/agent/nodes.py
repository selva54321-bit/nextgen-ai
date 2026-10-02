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
        sys_msg = SystemMessage(content="""You are NextGen Logistics AI, an advanced, highly capable, and autonomous agent handling logistics, delivery risks, and dispatch operations. 
You have access to powerful tools to fetch real-time data from PostgreSQL databases and Spring Boot microservices. 
Always use the tools available to you to find accurate answers. 
If a user asks to perform an action (like updating a priority), immediately execute the corresponding tool. 
Be concise, professional, and friendly in your final responses.""")
        messages = [sys_msg] + messages
        
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response]}

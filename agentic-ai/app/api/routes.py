from fastapi import APIRouter, Header
from pydantic import BaseModel
from typing import Optional
from ..agent.graph import build_graph
import uuid

router = APIRouter(prefix="/api/v1/agent", tags=["Agent"])

class QueryRequest(BaseModel):
    session_id: str
    user_id: str
    message: str

class QueryResponse(BaseModel):
    session_id: str
    status: str
    message: str
    tools_available: list[str]

graph = build_graph()

@router.post("/query", response_model=QueryResponse)
async def handle_query(req: QueryRequest, x_correlation_id: Optional[str] = Header(None)):
    corr_id = x_correlation_id or str(uuid.uuid4())
    
    from langchain_core.messages import HumanMessage
    state = await graph.ainvoke({
        "session_id": req.session_id,
        "user_id": req.user_id,
        "messages": [HumanMessage(content=req.message)],
        "correlation_id": corr_id,
        "errors": []
    }, config={"configurable": {"thread_id": req.session_id}})
    
    last_message = state["messages"][-1] if state.get("messages") else None
    raw_content = last_message.content if last_message else "Execution complete"
    
    if isinstance(raw_content, list):
        # Extract text components if it's a list
        texts = [str(item.get("text", "")) for item in raw_content if isinstance(item, dict) and "text" in item]
        response_text = " ".join(texts) if texts else str(raw_content)
    else:
        response_text = str(raw_content)
    
    return QueryResponse(
        session_id=req.session_id,
        status="INFRASTRUCTURE_READY",
        message=response_text,
        tools_available=[
            "get_dispatch_queue",
            "get_priority_orders",
            "get_delivery_risk",
            "update_order_priority"
        ]
    )

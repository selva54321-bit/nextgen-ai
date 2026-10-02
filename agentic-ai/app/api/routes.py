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
    })
    
    last_message = state["messages"][-1] if state.get("messages") else None
    response_text = last_message.content if last_message else "Execution complete"
    
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

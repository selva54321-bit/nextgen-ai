from fastapi import APIRouter
from pydantic import BaseModel
from ..agent.customer_graph import build_customer_graph
from ..schemas.customer import CustomerIntent

router = APIRouter(prefix="/api/v1/customer", tags=["Customer Workflow"])

class WorkflowRequest(BaseModel):
    session_id: str
    risk_level: str
    intent: CustomerIntent

class WorkflowResponse(BaseModel):
    session_id: str
    final_status: str
    message: str

graph = build_customer_graph()

@router.post("/workflow", response_model=WorkflowResponse)
async def handle_workflow(req: WorkflowRequest):
    state = await graph.ainvoke({
        "session_id": req.session_id,
        "risk_level": req.risk_level,
        "intent": req.intent
    })
    
    return WorkflowResponse(
        session_id=req.session_id,
        final_status=state.get("contact_status", "UNKNOWN"),
        message=state.get("response_msg", "Workflow complete")
    )

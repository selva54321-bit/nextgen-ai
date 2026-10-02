import os

files = {
    "agentic-ai/requirements.txt": """fastapi>=0.110.0
pydantic>=2.6.0
pydantic-settings>=2.2.0
uvicorn>=0.27.0
httpx>=0.27.0
langchain>=0.1.13
langgraph>=0.0.30
langchain-core>=0.1.33
sqlalchemy>=2.0.28
asyncpg>=0.29.0
tenacity>=8.2.3
pytest>=8.1.1
pytest-asyncio>=0.23.6
""",

    "agentic-ai/.env": """SPRING_BOOT_BASE_URL=http://localhost:8080
SPRING_BOOT_TIMEOUT_SECONDS=10
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/logistics
LOG_LEVEL=INFO
""",

    "agentic-ai/app/config.py": """from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SPRING_BOOT_BASE_URL: str = "http://localhost:8080"
    SPRING_BOOT_TIMEOUT_SECONDS: int = 10
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/logistics"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
""",

    "agentic-ai/app/schemas/agent.py": """from typing import TypedDict, Any

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
""",

    "agentic-ai/app/schemas/customer.py": """from enum import Enum
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
""",

    "agentic-ai/app/schemas/tools.py": """from pydantic import BaseModel
from typing import Literal

class ToolMetadata(BaseModel):
    name: str
    operation: Literal["READ", "WRITE"]
    requires_confirmation: bool
""",

    "agentic-ai/app/services/backend_client.py": """import httpx
from typing import Any
from ..config import settings
import logging

logger = logging.getLogger(__name__)

class BackendClient:
    def __init__(self):
        self.base_url = settings.SPRING_BOOT_BASE_URL
        self.timeout = settings.SPRING_BOOT_TIMEOUT_SECONDS

    async def _request(self, method: str, endpoint: str, correlation_id: str, **kwargs) -> dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        headers = kwargs.pop("headers", {})
        headers["X-Correlation-ID"] = correlation_id
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(method, url, headers=headers, **kwargs)
                response.raise_for_status()
                # If there's content, return json, else empty dict
                if response.content:
                    return response.json()
                return {}
            except httpx.HTTPError as e:
                logger.error(f"HTTP Request failed: {e}")
                raise
                
    async def get_dispatch_queue(self, correlation_id: str) -> dict[str, Any]:
        return await self._request("GET", "/api/v1/dispatch/queue", correlation_id)
        
    async def get_priority_orders(self, correlation_id: str) -> dict[str, Any]:
        return await self._request("GET", "/api/v1/dispatch/priority", correlation_id)
        
    async def get_delivery_risk(self, stop_id: str, correlation_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/api/v1/delivery/stops/{stop_id}/risk", correlation_id)
""",

    "agentic-ai/app/services/database.py": """from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import text
from ..config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class ReadOnlyDatabaseService:
    async def _execute_query(self, query: str, params: dict = None):
        async with AsyncSessionLocal() as session:
            result = await session.execute(text(query), params or {})
            return result.mappings().all()

    async def count_orders(self):
        result = await self._execute_query("SELECT count(*) as count FROM v_orders")
        return result[0]['count'] if result else 0

    async def count_dispatch_ready_orders(self):
        result = await self._execute_query("SELECT count(*) as count FROM v_dispatch_queue WHERE dispatch_ready = true")
        return result[0]['count'] if result else 0
        
    async def count_high_priority_orders(self):
        result = await self._execute_query("SELECT count(*) as count FROM v_dispatch_queue WHERE priority_tier = 'HIGH'")
        return result[0]['count'] if result else 0
""",

    "agentic-ai/app/security/action_guard.py": """from ..schemas.tools import ToolMetadata
import logging

logger = logging.getLogger(__name__)

class ActionGuard:
    @staticmethod
    def validate_action(metadata: ToolMetadata, user_permissions: list[str]) -> bool:
        if metadata.operation == "READ":
            return True
            
        if metadata.operation == "WRITE":
            # Check if user has permission
            if "WRITE_OPERATIONS" not in user_permissions:
                logger.warning(f"User lacks permission for WRITE operation: {metadata.name}")
                return False
                
            return True
        return False
""",

    "agentic-ai/app/tools/dispatch_tools.py": """from langchain_core.tools import tool
from ..services.backend_client import BackendClient
from ..schemas.tools import ToolMetadata

get_dispatch_queue_meta = ToolMetadata(name="get_dispatch_queue", operation="READ", requires_confirmation=False)

@tool
async def get_dispatch_queue(correlation_id: str) -> dict:
    \"\"\"Gets the current dispatch queue\"\"\"
    client = BackendClient()
    try:
        return await client.get_dispatch_queue(correlation_id)
    except Exception as e:
        return {"error": str(e)}

get_priority_orders_meta = ToolMetadata(name="get_priority_orders", operation="READ", requires_confirmation=False)

@tool
async def get_priority_orders(correlation_id: str) -> dict:
    \"\"\"Gets high priority orders\"\"\"
    client = BackendClient()
    try:
        return await client.get_priority_orders(correlation_id)
    except Exception as e:
        return {"error": str(e)}
""",
    
    "agentic-ai/app/tools/delivery_tools.py": """from langchain_core.tools import tool
from ..services.backend_client import BackendClient
from ..schemas.tools import ToolMetadata

get_delivery_risk_meta = ToolMetadata(name="get_delivery_risk", operation="READ", requires_confirmation=False)

@tool
async def get_delivery_risk(stop_id: str, correlation_id: str) -> dict:
    \"\"\"Gets the delivery risk for a specific stop\"\"\"
    client = BackendClient()
    try:
        return await client.get_delivery_risk(stop_id, correlation_id)
    except Exception as e:
        return {"error": str(e)}
""",

    "agentic-ai/app/agent/nodes.py": """from .state import AgentState
from ..tools.dispatch_tools import get_dispatch_queue, get_priority_orders
from ..tools.delivery_tools import get_delivery_risk
import logging

logger = logging.getLogger(__name__)

async def validate_request(state: AgentState) -> dict:
    logger.info("Validating request")
    if not state.get("user_message"):
        return {"errors": ["User message is empty"]}
    return {}

async def load_context(state: AgentState) -> dict:
    logger.info("Loading context")
    return {"context": {"system": "logistics"}}

async def intent_router(state: AgentState) -> dict:
    logger.info("Routing intent")
    msg = state.get("user_message", "").lower()
    
    if "how many orders" in msg or "waiting for dispatch" in msg:
        return {"intent": "GET_DISPATCH_QUEUE", "selected_tool": "get_dispatch_queue"}
    elif "priority" in msg:
        return {"intent": "GET_PRIORITY_ORDERS", "selected_tool": "get_priority_orders"}
    elif "delivery risk" in msg:
        return {"intent": "GET_DELIVERY_RISK", "selected_tool": "get_delivery_risk"}
    else:
        return {"intent": "UNKNOWN"}

async def tool_selection(state: AgentState) -> dict:
    logger.info("Selecting tool")
    return {}

async def permission_check(state: AgentState) -> dict:
    logger.info("Checking permissions")
    return {"action_allowed": True}

async def tool_execution(state: AgentState) -> dict:
    logger.info("Executing tool")
    tool_output = {}
    errors = state.get("errors", [])
    if state.get("action_allowed") and state.get("selected_tool"):
        tool_name = state["selected_tool"]
        correlation_id = state.get("correlation_id", "default-corr-id")
        
        try:
            if tool_name == "get_dispatch_queue":
                tool_output = await get_dispatch_queue.ainvoke({"correlation_id": correlation_id})
            elif tool_name == "get_priority_orders":
                tool_output = await get_priority_orders.ainvoke({"correlation_id": correlation_id})
            elif tool_name == "get_delivery_risk":
                tool_output = await get_delivery_risk.ainvoke({"stop_id": "B-24.2C", "correlation_id": correlation_id})
        except Exception as e:
            errors.append(str(e))
    return {"tool_output": tool_output, "errors": errors}

async def result_normalization(state: AgentState) -> dict:
    logger.info("Normalizing result")
    if state.get("tool_output"):
        return {"execution_result": {"raw": state.get("tool_output")}}
    return {}

async def response_builder(state: AgentState) -> dict:
    logger.info("Building response")
    return {"response": "Agent graph executed without LLM reasoning"}
""",

    "agentic-ai/app/agent/graph.py": """from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .nodes import (
    validate_request,
    load_context,
    intent_router,
    tool_selection,
    permission_check,
    tool_execution,
    result_normalization,
    response_builder
)

def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("validate_request", validate_request)
    workflow.add_node("load_context", load_context)
    workflow.add_node("intent_router", intent_router)
    workflow.add_node("tool_selection", tool_selection)
    workflow.add_node("permission_check", permission_check)
    workflow.add_node("tool_execution", tool_execution)
    workflow.add_node("result_normalization", result_normalization)
    workflow.add_node("response_builder", response_builder)
    
    workflow.add_edge(START, "validate_request")
    workflow.add_edge("validate_request", "load_context")
    workflow.add_edge("load_context", "intent_router")
    workflow.add_edge("intent_router", "tool_selection")
    workflow.add_edge("tool_selection", "permission_check")
    workflow.add_edge("permission_check", "tool_execution")
    workflow.add_edge("tool_execution", "result_normalization")
    workflow.add_edge("result_normalization", "response_builder")
    workflow.add_edge("response_builder", END)
    
    return workflow.compile()
""",

    "agentic-ai/app/api/routes.py": """from fastapi import APIRouter, Header
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
    
    state = await graph.ainvoke({
        "session_id": req.session_id,
        "user_id": req.user_id,
        "user_message": req.message,
        "correlation_id": corr_id,
        "errors": []
    })
    
    return QueryResponse(
        session_id=req.session_id,
        status="INFRASTRUCTURE_READY",
        message=state.get("response", "Execution complete"),
        tools_available=[
            "get_dispatch_queue",
            "get_priority_orders",
            "get_delivery_risk"
        ]
    )
""",

    "agentic-ai/app/main.py": """from fastapi import FastAPI
from .api import routes

app = FastAPI(title="Agentic AI Wrapper", version="1.0.0")

app.include_router(routes.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
"""
}

for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

print("Scaffolding completed.")

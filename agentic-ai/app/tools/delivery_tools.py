from langchain_core.tools import tool
from ..services.backend_client import BackendClient
from ..schemas.tools import ToolMetadata

get_delivery_risk_meta = ToolMetadata(name="get_delivery_risk", operation="READ", requires_confirmation=False)

@tool
async def get_delivery_risk(stop_id: str, correlation_id: str) -> dict:
    """Gets the delivery risk for a specific stop"""
    client = BackendClient()
    try:
        return await client.get_delivery_risk(stop_id, correlation_id)
    except Exception as e:
        return {"error": str(e)}

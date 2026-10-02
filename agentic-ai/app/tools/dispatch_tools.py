from langchain_core.tools import tool
from ..services.backend_client import BackendClient
from ..schemas.tools import ToolMetadata

get_dispatch_queue_meta = ToolMetadata(name="get_dispatch_queue", operation="READ", requires_confirmation=False)

@tool
async def get_dispatch_queue(correlation_id: str) -> dict:
    """Gets the current dispatch queue"""
    client = BackendClient()
    try:
        return await client.get_dispatch_queue(correlation_id)
    except Exception as e:
        return {"error": str(e)}

get_priority_orders_meta = ToolMetadata(name="get_priority_orders", operation="READ", requires_confirmation=False)

@tool
async def get_priority_orders(correlation_id: str) -> dict:
    """Gets high priority orders"""
    client = BackendClient()
    try:
        return await client.get_priority_orders(correlation_id)
    except Exception as e:
        return {"error": str(e)}

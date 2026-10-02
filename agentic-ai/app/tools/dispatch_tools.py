from langchain_core.tools import tool
from ..services.backend_client import BackendClient
from ..schemas.tools import ToolMetadata

get_dispatch_queue_meta = ToolMetadata(name="get_dispatch_queue", operation="READ", requires_confirmation=False)

@tool
async def get_dispatch_queue(correlation_id: str) -> dict:
    """Gets the current dispatch queue from the database"""
    from ..services.database import ReadOnlyDatabaseService
    db = ReadOnlyDatabaseService()
    try:
        count = await db.count_dispatch_ready_orders()
        return {"dispatch_ready_orders": count, "message": f"{count} orders are waiting in the queue."}
    except Exception as e:
        return {"error": str(e)}

get_priority_orders_meta = ToolMetadata(name="get_priority_orders", operation="READ", requires_confirmation=False)

@tool
async def get_priority_orders(correlation_id: str) -> dict:
    """Gets high priority orders from the database"""
    from ..services.database import ReadOnlyDatabaseService
    db = ReadOnlyDatabaseService()
    try:
        count = await db.count_high_priority_orders()
        return {"high_priority_orders": count, "message": f"{count} high priority orders found."}
    except Exception as e:
        return {"error": str(e)}

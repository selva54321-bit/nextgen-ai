from langchain_core.tools import tool
from ..services.backend_client import BackendClient
from ..schemas.tools import ToolMetadata

update_order_priority_meta = ToolMetadata(name="update_order_priority", operation="WRITE", requires_confirmation=True)

@tool
async def update_order_priority(order_id: str, new_priority: str, correlation_id: str) -> dict:
    """Updates the priority of a specific order."""
    # Assuming this might call a backend endpoint in the real world
    return {"status": "SUCCESS", "message": f"Order {order_id} priority updated to {new_priority}"}

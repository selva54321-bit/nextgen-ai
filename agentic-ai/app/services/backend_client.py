import httpx
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

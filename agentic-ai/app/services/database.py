from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
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

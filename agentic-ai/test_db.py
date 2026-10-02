import asyncio
from app.services.database import ReadOnlyDatabaseService

async def main():
    db = ReadOnlyDatabaseService()
    try:
        res = await db._execute_query("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        print("Tables in public schema:")
        for r in res:
            print(f"- {r['table_name']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

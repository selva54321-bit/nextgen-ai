import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres.rgkngmdpoylnupcebqlf:HarishSathiya%4007@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"

async def main():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            ORDER BY table_name, ordinal_position;
        """))
        
        current_table = None
        for row in result:
            table_name, column_name, data_type = row
            if table_name != current_table:
                print(f"\nTable: {table_name}")
                current_table = table_name
            print(f"  - {column_name}: {data_type}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())

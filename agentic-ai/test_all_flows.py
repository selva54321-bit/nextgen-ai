import httpx
import asyncio
import uuid
import json

BASE_URL = "http://10.10.66.62:8000/api/v1/agent/query"

async def test_condition(name: str, message: str):
    print(f"\n--- Testing Condition: {name} ---")
    print(f"User Message: {message}")
    
    payload = {
        "session_id": f"sess-{uuid.uuid4()}",
        "user_id": "operator",
        "message": message
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(BASE_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            print(f"Agent Response: {data.get('message')}")
        except Exception as e:
            print(f"Error testing condition: {e}")

async def main():
    # Condition 1: Fetching Dispatch Queue from Database
    await test_condition(
        "Dispatch Queue", 
        "How many orders are waiting for dispatch right now?"
    )
    
    # Condition 2: Fetching Delivery Risk from Java Backend
    await test_condition(
        "Delivery Risk", 
        "Can you check the delivery risk for stop B-24.2C?"
    )
    
    # Condition 3: Fetching Priority Orders from Database
    await test_condition(
        "Priority Orders", 
        "How many high priority orders do we have?"
    )
    
    # Condition 4: Action Tool (Mutation)
    await test_condition(
        "Update Priority", 
        "Please update the priority of order ORD-5542 to HIGH."
    )
    
    # Condition 5: Unrelated / Fallback
    await test_condition(
        "Unrelated Query", 
        "What is the weather like today?"
    )

if __name__ == "__main__":
    asyncio.run(main())

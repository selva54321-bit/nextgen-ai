import asyncio
from app.agent.graph import build_graph
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    graph = build_graph()
    corr_id = str(uuid.uuid4())
    
    from langchain_core.messages import HumanMessage
    state = await graph.ainvoke({
        "session_id": "sess-test",
        "user_id": "user-test",
        "messages": [HumanMessage(content="how many orders are waiting for dispatch?")],
        "correlation_id": corr_id,
        "errors": []
    })
    
    print("Agent State Output:")
    for m in state.get("messages", []):
        m.pretty_print()

if __name__ == "__main__":
    asyncio.run(main())

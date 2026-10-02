from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_agent_query():
    response = client.post("/api/v1/agent/query", json={
        "session_id": "sess-1",
        "user_id": "user-1",
        "message": "how many orders"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "INFRASTRUCTURE_READY"

def test_customer_workflow():
    response = client.post("/api/v1/customer/workflow", json={
        "session_id": "sess-1",
        "risk_level": "HIGH",
        "intent": "MAYBE"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["final_status"] == "CONFIRMATION_PENDING"

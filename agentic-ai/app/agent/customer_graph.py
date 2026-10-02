from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Any
from ..schemas.customer import CustomerIntent

class CustomerState(TypedDict, total=False):
    session_id: str
    risk_level: str
    contact_status: str
    customer_response: str
    intent: CustomerIntent
    delivery_window: str
    alternative_slots: list[str]
    errors: list[str]
    response_msg: str

async def init_contact(state: CustomerState) -> dict:
    if state.get("risk_level") == "HIGH":
        return {"contact_status": "CONTACT_INITIATED", "response_msg": "Contact Initiated"}
    return {"contact_status": "NO_ACTION"}

async def wait_for_response(state: CustomerState) -> dict:
    return {"contact_status": "WAITING_FOR_RESPONSE"}

async def process_intent(state: CustomerState) -> dict:
    intent = state.get("intent", CustomerIntent.UNKNOWN)
    if intent == CustomerIntent.CONFIRM:
        return {"contact_status": "WINDOW_LOCKED", "response_msg": "Window Locked. Delivery Continues."}
    elif intent == CustomerIntent.MAYBE:
        return {"contact_status": "CONFIRMATION_PENDING", "response_msg": "Wait for checkpoint."}
    elif intent == CustomerIntent.NOT_AVAILABLE:
        return {"contact_status": "GENERATE_ALTERNATIVES", "response_msg": "Generating Alternatives..."}
    elif intent == CustomerIntent.NO_RESPONSE:
        return {"contact_status": "REMINDER_SENT", "response_msg": "Reminder Sent."}
    return {"contact_status": "FALLBACK_POLICY"}

def build_customer_graph():
    workflow = StateGraph(CustomerState)
    
    workflow.add_node("init_contact", init_contact)
    workflow.add_node("wait_for_response", wait_for_response)
    workflow.add_node("process_intent", process_intent)
    
    workflow.add_edge(START, "init_contact")
    workflow.add_edge("init_contact", "wait_for_response")
    workflow.add_edge("wait_for_response", "process_intent")
    workflow.add_edge("process_intent", END)
    
    return workflow.compile()

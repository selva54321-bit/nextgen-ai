from fastapi import FastAPI
from .api import routes
from .api import customer_routes

app = FastAPI(title="Agentic AI Wrapper", version="1.0.0")

app.include_router(routes.router)
app.include_router(customer_routes.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

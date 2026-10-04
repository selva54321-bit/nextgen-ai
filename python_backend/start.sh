#!/bin/bash
# Start both FastAPI apps

# First Attempt Failure Engine (predicts delivery risk)
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Warehouse Priority Engine
uvicorn priorityEndPoint:app --host 0.0.0.0 --port 8001 &

# Wait for both background processes
wait -n

# Exit with status of process that exited first
exit $?

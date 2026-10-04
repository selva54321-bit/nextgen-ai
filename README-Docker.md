# NextGen Logistics AI - Docker Deployment

This repository provides a complete Docker-based deployment setup for the three main services of the NextGen Logistics AI application.

## Architecture

```text
                    ┌─────────────────────┐
                    │      Client/UI      │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ application_backend │
                    │    Spring Boot      │
                    └───────┬───────┬──────┘
                            │       │
                            │       └──────────────┐
                            │                      │
                            ▼                      ▼
                   ┌────────────────┐      Cloud PostgreSQL
                   │ python_backend │
                   │    FastAPI     │
                   │   ML Models    │
                   └────────────────┘

                    Agentic AI
                         │
                         ▼
                   ┌─────────────┐
                   │ agentic_ai  │
                   │ LangChain   │
                   │ LangGraph   │
                   └──────┬──────┘
                          │
                          │ HTTP API
                          ▼
                   application_backend
```

## Directory Structure

*   `Application-Backend/`: Java Spring Boot backend (Core service)
*   `python_backend/`: Python FastAPI service hosting the ML models for delivery prediction and warehouse priority.
*   `agentic-ai/`: Python FastAPI Agentic AI wrapper using LangChain/LangGraph.
*   `docker-compose.yml`: Main deployment file defining the three services and their network.
*   `.env.example`: Template for environment variables needed by the services.

## Prerequisites

1.  Docker
2.  Docker Compose (v2)

## Environment Variables

Copy `.env.example` to `.env` and fill in the necessary details:

```bash
cp .env.example .env
```

Variables required:
*   `DATABASE_URL`: JDBC URL for PostgreSQL (for Spring Boot).
*   `DATABASE_USERNAME` & `DATABASE_PASSWORD`: Credentials for the DB.
*   `AGENTIC_DB_URL`: asyncpg URL for PostgreSQL (for Agentic AI).
*   `GEMINI_API_KEY`: API key for the LLM.
*   `TWILIO_*` / `WHATSAPP_*`: Twilio integration settings.

## Build and Start

To build the images:
```bash
docker compose build
```

To start the containers in the background:
```bash
docker compose up -d
```

## Stop

To stop the containers:
```bash
docker compose down
```

## Logs

To view the logs of all services:
```bash
docker compose logs -f
```

To view logs for a specific service:
```bash
docker compose logs -f application_backend
docker compose logs -f python_backend
docker compose logs -f agentic_ai
```

## Service URLs

**External URLs (accessible from host):**
*   `application_backend`: http://localhost:8080
*   `python_backend`: http://localhost:8000 and http://localhost:8001
*   `agentic_ai`: http://localhost:8002

**Internal Docker URLs (service-to-service communication):**
*   `application_backend`: http://application_backend:8080
*   `python_backend` Delivery Predict: http://python_backend:8000
*   `python_backend` Warehouse Priority: http://python_backend:8001
*   `agentic_ai`: http://agentic_ai:8002

## Cloud PostgreSQL Configuration

The application uses an external, cloud-hosted PostgreSQL database on Supabase.
No local PostgreSQL container is deployed. Both the `application_backend` and `agentic_ai` connect directly to this external DB using their respective JDBC and asyncpg drivers.

## Communication Flow

1.  **application_backend to python_backend**: The Spring Boot app communicates with the Python ML endpoints using HTTP REST. The URLs are configured via environment variables (`PYTHON_BACKEND_DELIVERY_URL` and `PYTHON_BACKEND_WAREHOUSE_URL`) inside the Docker network.
2.  **agentic_ai to application_backend**: The LangGraph Agent executes tools by communicating with the Spring Boot backend via HTTP APIs, utilizing the internal Docker URL `http://application_backend:8080`.

## Troubleshooting

1.  **Database Connection Refused**: Ensure that your cloud PostgreSQL instance is accessible from your network and the credentials in `.env` are correct.
2.  **Port Conflicts**: If ports 8080, 8000, 8001, or 8002 are already in use on your host, you can map them to different ports in `docker-compose.yml`.
3.  **OutOfMemory Errors**: Spring Boot and Python ML models require sufficient memory. If containers exit unexpectedly with OOMKill, try increasing Docker's memory limit.

## Verifying Services

You can verify that all services are healthy by accessing their health/root endpoints:
*   Java Backend: `http://localhost:8080/`
*   Python ML Backend (Delivery): `http://localhost:8000/`
*   Python ML Backend (Priority): `http://localhost:8001/health`
*   Agentic AI: `http://localhost:8002/health`

# NextGen Logistics AI: Backend & Database Context

This document provides a comprehensive overview of the `Application-Backend` (Spring Boot microservice) and the PostgreSQL Database schema. It is designed to be provided as context to other AI agents or developers working on the NextGen AI project.

---

## 1. Architecture Overview
The NextGen Logistics platform uses a modular architecture:
1. **Spring Boot Backend (`Application-Backend`)**: Handles warehouse data ingestion, simulations, dispatch planning, and delivery risk tracking.
2. **PostgreSQL Database (Supabase)**: Stores relational data for orders, dispatches, shipments, WhatsApp communications, and recommendations.
3. **Agentic AI Wrapper (`agentic-ai`)**: A FastAPI + LangGraph Python service that acts as an autonomous AI orchestrator. It queries the PostgreSQL database natively for read operations and sends HTTP requests to the Spring Boot backend to interact with logic/endpoints.

---

## 2. PostgreSQL Database Schema
The cloud database schema is stored in the `public` schema and contains the following tables and columns:

### Core Logistics Tables
*   **`orders`**: 
    *   `order_id` (VARCHAR)
    *   `customer_id` (VARCHAR)
    *   `status` (VARCHAR) - e.g., 'PRIORITY'
    *   `deadline` (TIMESTAMP)
    *   `created_at` (TIMESTAMP)
*   **`dispatch_assignments`**:
    *   `order_id` (VARCHAR)
    *   `unit_id` (VARCHAR)
    *   `status` (VARCHAR) - e.g., 'PENDING'
    *   `assigned_at` (TIMESTAMP)
    *   `planned_departure` (TIMESTAMP)
*   **`dispatch_units`**:
    *   `unit_id` (VARCHAR)
    *   `capacity` (DOUBLE)
    *   `availability` (VARCHAR)
    *   `current_location` (VARCHAR)
*   **`shipment_data`**:
    *   `id` (UUID)

### WhatsApp / Communication Tables
*   **`whatsapp_messages`**:
    *   `id` (BIGINT)
    *   `phone_number` (VARCHAR)
    *   `message_content` (VARCHAR)
    *   `message_type` (VARCHAR)
    *   `direction` (VARCHAR)
    *   `provider` (VARCHAR)
    *   `provider_message_id` (VARCHAR)
    *   `status` (VARCHAR)
    *   `created_at` (TIMESTAMP)
    *   `updated_at` (TIMESTAMP)
*   **`whatsapp_interactions`**:
    *   `id` (BIGINT)
    *   `whatsapp_message_id` (BIGINT)
    *   `interaction_type` (VARCHAR)
    *   `response_value` (VARCHAR)
    *   `shipment_id_context` (VARCHAR)
    *   `created_at` (TIMESTAMP)

### AI Recommendation Tables
*   **`recommendations`**:
    *   `id` (BIGINT)
    *   `shipment_id` (VARCHAR)
    *   `recommendation_type` (VARCHAR)
    *   `risk_level` (VARCHAR)
    *   `risk_score` (DOUBLE)
    *   `reason` (VARCHAR)
    *   `channel` (VARCHAR)
    *   `status` (VARCHAR)
    *   `created_at` (TIMESTAMP)
    *   `updated_at` (TIMESTAMP)

---

## 3. Spring Boot Application Backend (`Application-Backend`)
The Java backend exposes REST APIs across three primary domains. It is conventionally hosted at `http://10.10.66.62:8080/api/v1/`.

### Controllers & Endpoints

#### 1. `DispatchController` (`/api/v1/dispatch`)
Handles AI-driven dispatch planning logic.
*   **`POST /plan`**: Accepts a `DispatchPlanRequest` and returns a `DispatchPlanResponse`. (Executes logic in `DispatchService`).

#### 2. `WarehouseController` (`/api/v1/warehouse`)
Handles dataset ingestion, facility simulations, and picking prioritization.
*   **`POST /upload`**: Accepts a multi-part `file` and processes it via `DataIngestionService`. Returns upload statistics.
*   **`POST /simulations`**: Triggers a warehouse simulation job.
*   **`POST /picking/rank`**: Retrieves AI-ranked task priorities (e.g., returns high priority picking tasks).

#### 3. `DeliveryController` (`/api/v1/delivery`)
Manages downstream delivery predictions and risk assessments.
*   **`POST /predictions`**: Persists AI delivery predictions.
*   **`GET /stops/{id}/risk`**: Retrieves the risk level and failure probability for a specific delivery stop ID (e.g., returns `{"riskBand": "MEDIUM", "failureProbability": 0.034}`).
*   **`POST /events`**: Records ongoing delivery events (success, failure, transit milestones).

### Key Java Packages
*   `com.ai_nextgen_hacks.main.controllers`: Exposes API routes.
*   `com.ai_nextgen_hacks.main.services`: Business logic (`DispatchService`, `DataIngestionService`).
*   `com.ai_nextgen_hacks.main.models`: JPA Entities mapped to the PostgreSQL database (`Order`, `DispatchAssignment`, `DispatchUnit`, `ShipmentData`).
*   `com.ai_nextgen_hacks.main.repos`: Spring Data JPA interfaces.
*   `com.ai_nextgen_hacks.main.whatsapp`: WhatsApp Twilio integration and message webhooks.
*   `com.ai_nextgen_hacks.main.recommendation`: Recommendation engine logic.

---

## 4. Integration Note
The `agentic-ai` Python orchestrator connects these two pieces:
1. **Reads**: It directly queries the database tables (e.g., `orders`, `dispatch_assignments`) using `SQLAlchemy (asyncpg)` for high-speed data fetching.
2. **Writes/Logic**: It defers to the `Application-Backend` APIs using HTTP requests for complex operations (e.g., dispatch planning, delivery risk checking).
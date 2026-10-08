# CareFlow — Architecture Diagram

```mermaid
flowchart TB
    subgraph Client["Client Devices"]
        Browser["Staff Browser<br/>(React SPA)"]
        Kiosk["Public Kiosk Display<br/>(React, no auth)"]
    end

    subgraph Edge["Edge"]
        Nginx["Nginx<br/>reverse proxy + static React build"]
    end

    subgraph App["Application Layer"]
        Django["Django + DRF<br/>REST API"]
        Daphne["Daphne (ASGI)<br/>serves HTTP + WebSocket"]
        Channels["Django Channels<br/>WebSocket consumer<br/>(live queue board)"]
    end

    subgraph Async["Async Workers"]
        CeleryWorker["Celery Worker"]
        CeleryBeat["Celery Beat<br/>(5-min schedule)"]
    end

    subgraph ML["ML Microservice"]
        FastAPI["FastAPI"]
        WaitModel["Gradient Boosting<br/>wait-time model"]
        OvercrowdModel["Holt-Winters + GBR<br/>overcrowding forecast"]
        Staffing["Rule-based<br/>staffing recommender"]
    end

    subgraph Data["Data Layer"]
        Postgres[("PostgreSQL<br/>Patient/Department/Staff/Alert data")]
        Redis[("Redis<br/>Celery broker + cache + Channels layer")]
    end

    Browser -->|HTTPS| Nginx
    Kiosk -->|HTTPS, public endpoint only| Nginx
    Nginx -->|"/api/*"| Django
    Nginx -->|"/ws/*"| Daphne
    Django <-.->|ASGI process| Daphne
    Daphne --> Channels
    Channels <-->|pub/sub| Redis

    Django -->|ORM| Postgres
    Django -->|proxies /predictions/*| FastAPI
    Django -->|enqueues periodic checks| Redis
    CeleryWorker -->|consumes tasks| Redis
    CeleryBeat -->|schedules| Redis
    CeleryWorker -->|writes Alerts| Postgres

    FastAPI --> WaitModel
    FastAPI --> OvercrowdModel
    FastAPI --> Staffing

    style Postgres fill:#0ea5a5,color:#fff
    style Redis fill:#dc2626,color:#fff
    style FastAPI fill:#14c9c9,color:#0b1830
    style Django fill:#0b1830,color:#fff
```

## Request flow — patient intake to live board update

```mermaid
sequenceDiagram
    participant Nurse as Nurse (Browser)
    participant API as Django REST API
    participant DB as PostgreSQL
    participant WS as Channels (WebSocket)
    participant Board as Live Queue Board (any connected browser)

    Nurse->>API: POST /patients/intake {triage_level, department}
    API->>API: RBAC check (NURSE or ADMIN only)
    API->>DB: Create Patient + QueueEvent(INTAKE)
    API->>WS: channel_layer.group_send("queue_<dept_id>")
    WS-->>Board: {"type": "queue_update", "department_id": ...}
    Board->>API: GET /departments/:id/queue (refetch)
    API->>DB: SELECT waiting patients
    API-->>Board: Updated patient list
```

## Why this shape

- **Django owns the source of truth** (Postgres) and all writes; the
  FastAPI service is stateless and only ever proxied *through* Django's
  `/predictions/*` endpoints — the React frontend never calls FastAPI
  directly. This keeps auth/RBAC in one place and lets Django log every
  prediction to the `Prediction` table for the model-accuracy dashboard.
- **WebSocket messages are signals, not data.** The Channels consumer
  pushes `{"type": "queue_update"}` with no patient fields in it, so
  the live board always re-fetches through the authenticated REST API
  rather than receiving patient data over a channel that isn't
  individually access-controlled per viewer.
- **Celery Beat is the safety net, not the primary path.** Overcrowding
  alerts are recomputed every 5 minutes regardless of whether anyone is
  actively calling `/predictions/overcrowding-risk`, so a quiet shift
  still gets flagged if bed occupancy quietly creeps past 95%.

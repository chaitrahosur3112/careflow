# CareFlow — AI-Powered Hospital Patient Flow & Resource Allocation Platform

> Academic final-year portfolio project. Focus: hospital **operations** —
> queue management, bed/staff allocation, wait-time & overcrowding
> prediction. No medical records, diagnoses, or prescriptions are modeled
> or stored anywhere in this system.

## ⚠️ Disclaimer

This is an academic portfolio project for demonstration purposes only.
It is **not** a certified medical device and is **not** HIPAA-compliant
for real clinical deployment without further legal, security, and
compliance engineering. No real patient data is used or stored — all
demo data is fully synthetic. Clinical decisions must never be made
based on this system's output.

## Build status — All 4 phases complete

This zip is the full CareFlow build: **Django backend**, **FastAPI ML
microservice**, **React + Tailwind frontend**, and now **Docker
Compose, CI/CD, seed data, and docs**.

### Phase 1 — Django backend
**Included and verified (migrations generate cleanly, `manage.py check` passes):**
- Full project/app folder structure (`backend/apps/*`)
- Custom `User` model with roles (Admin, Doctor, Nurse, Hospital
  Administrator) + JWT auth (access/refresh, bcrypt hashing, blacklist
  on logout)
- Models: `Department`, `Patient`, `QueueEvent` (audit trail),
  `StaffShift`, `Prediction`, `Alert`
- DRF serializers + views + URLs for every module in the spec: auth,
  patients/queue, departments, staff, predictions (proxy to the future
  FastAPI service), alerts, analytics, and the **public, unauthenticated
  kiosk endpoint** (field-locked — anonymized wait times only)
- RBAC permission classes enforced per-endpoint (`apps/patients/permissions.py`)
- Django Channels WebSocket consumer + routing for the live queue board
- Celery task + Beat schedule for periodic overcrowding/long-wait alert checks
- Redis wired in for cache (shared, required by `django-ratelimit`),
  Celery broker, and Channels layer
- Rate limiting on auth and kiosk endpoints
- `.env.example` — nothing is hardcoded

### Phase 2 — FastAPI ML microservice
**Included and verified (both models trained end-to-end on synthetic
data, every endpoint hit and checked for sane output — see
`ml_service/README.md` for full detail):**
- `data_generator.py` — synthetic wait-time + occupancy-time-series
  generators (no real hospital data anywhere)
- `train.py` — trains both models, evaluates on a held-out split, saves
  `artifacts/*.pkl` + `metrics.json`
- Wait-time model: Gradient Boosting Regressor — **MAE ≈ 3.4 min, R² ≈ 0.99**
- Overcrowding-risk model: Gradient Boosting Regressor trained on
  statsmodels Holt-Winters-smoothed 2h-ahead occupancy forecasts,
  blended with live occupancy for calibrated `low`/`amber`/`red` severity
- `/recommend/staffing` — explainable, rule-based plain-English
  recommendations; `current_load` is documented as a patient-count
  (queue length), and the suggested staff addition is capped at a
  realistic per-shift ceiling so it never proposes something absurd
  like "add 18 nurses"
- `/model/metrics` — for the Admin dashboard's model-validation display
- FastAPI app with CORS locked to the Django origin, model loading once
  at startup (not per-request)

### Phase 3 — React frontend
**Included and verified (`npm run build` produces a clean production bundle):**
- Vite + React 19 + Tailwind CSS v4 (`@tailwindcss/vite`), Framer
  Motion, Recharts, lucide-react, axios, react-router-dom
- **Deviation from spec, with reason:** the spec listed
  `socket.io-client`, but the Django backend uses Channels (plain
  WebSocket protocol) — not socket.io-compatible without adding a
  Node layer. The frontend uses the native browser `WebSocket` API
  instead (`src/lib/useQueueSocket.js`), talking directly to the
  Channels consumer with no extra dependency.
- Dark navy / cyan-teal theme, light/dark toggle (persisted),
  glassmorphism cards, amber/red load-color system throughout
- **14 pages**: Landing (with the "Predict. Allocate. Save Lives."
  tagline), Login, Register (Admin-only — moved behind auth; the spec
  says admin-only but a public route would let anyone attempt it),
  role-aware Dashboard, Live Queue Board (WebSocket-live, toasts on
  updates), Patient Intake, Department Management, Staff Management
  (staff picked from a real dropdown, not a raw UUID field),
  AI Predictions (calls the FastAPI service through Django, shows the
  risk gauge + model accuracy for Admins), Analytics & Reports
  (admission trends, peak-hour heatmap, bottleneck table), Alerts Log,
  Kiosk View (public, no auth, polls every 30s), Profile & Settings,
  Admin Panel (staff directory + create/deactivate accounts)
- Role-based navigation and route guards (`RoleRoute.jsx`) matching the
  backend's RBAC exactly — e.g. a Nurse never sees the Admin Panel link
- JWT access/refresh handled transparently in `src/lib/api.js` — a 401
  triggers a silent refresh-and-retry, redirecting to `/login` only if
  the refresh itself fails
- **One backend addition made to support this phase**: `GET /users/all`
  and `GET/PATCH/DELETE /users/:id` (Admin-only) didn't exist yet — the
  Admin Panel needs a staff directory to manage. Added to
  `apps/users/`. Deleting a user soft-deactivates rather than
  hard-deletes, to preserve the `QueueEvent`/`Alert` audit trail.
- **Bug caught and fixed while wiring this up**: the Phase 2 staffing
  recommendation could suggest something unrealistic like "add 18
  nurses" if `current_load` was misread as a percentage instead of a
  queue-length count. Fixed in `ml_service/app/ml/staffing.py` (units
  documented, output capped) and mirrored in the Django serializer's
  docstring so both services agree on the contract.
- `.env.example` for `VITE_API_BASE_URL` / `VITE_WS_BASE_URL`

### Phase 4 — Docker Compose, CI/CD, seed data, docs
**Included and verified (see below for exactly how each piece was tested):**
- `docker/docker-compose.yml` — all 7 services: Postgres, Redis, the ML
  service, Django (served by **Daphne**, not `runserver`, since ASGI is
  required for WebSockets), a Celery worker, Celery beat, and Nginx
  serving the built React app and reverse-proxying `/api/` + `/ws/` to
  Django. YAML-validated; not run live in this environment (no Docker
  daemon available in the build sandbox) — verify with `docker compose
  up --build` on your machine.
- `backend/entrypoint.sh` waits for Postgres, runs migrations, then starts
  Daphne. It does not create administrator accounts automatically. Use
  `python manage.py bootstrap_admin` with a confirmed database host for
  one-time admin setup.
- **Real backend test suite added** (`apps/patients/tests.py`) — 8
  tests, all passing: kiosk-endpoint field-lockdown (asserts the
  response can *only* ever contain the 3 anonymized fields), RBAC
  rejection for unauthenticated/wrong-role intake attempts, and
  department stat computation. This is what `manage.py test` in CI
  actually runs — not a placeholder.
- **Real ML service test suite added** (`ml_service/tests/`) — 5
  tests, all passing, including a regression test that pins down the
  Phase 3 staffing-recommendation bug so it can't come back.
- `.github/workflows/ci-cd.yml` — lint → Django check → migration
  check → test (backend), lint → pytest (ML service), and build
  (frontend) run in parallel; only on success does it build and push
  all three Docker images to GHCR. The final AWS deploy step is an
  explicit, documented placeholder — there's no live cloud account
  behind this project to deploy to.
- `seed_data/seed.py` — creates 4 departments, 7 staff accounts across
  every role, ~45 patients with realistic status/triage distributions,
  QueueEvent audit trails, and active staff shifts. **Actually run
  against a live SQLite/Postgres DB during development, including a
  rerun to confirm idempotency** — the first version doubled patient
  counts on rerun (deleting by a nurse FK that gets orphaned when users
  are recreated); fixed to clear by department instead, which is
  stable across reruns.
- `docs/architecture.md` — Mermaid system diagram + a sequence diagram
  for the intake → WebSocket → live-board-refetch flow, with a "why
  this shape" section
- `docs/viva-qa-guide.md` — organized by module (architecture, auth/RBAC,
  data model, real-time, Celery, ML, security, deployment), plus an
  explicit "honest limitations" section to raise before it's asked

## Getting started — full stack via Docker Compose

```bash
cp docker/.env.example docker/.env       # shared Postgres creds
cp backend/.env.example backend/.env     # fill in DJANGO_SECRET_KEY at minimum
cp ml_service/.env.example ml_service/.env
cd docker
docker compose up --build
```

- Frontend: http://localhost — Nginx serves the React build and
  proxies `/api/` and `/ws/` to the backend
- Backend API directly: http://localhost:8000
- ML service directly: http://localhost:8001/docs (FastAPI's Swagger UI)
- Kiosk view: http://localhost/kiosk

Then seed demo data (run once, from inside the backend container or
your local venv against the same DB):

```bash
docker compose exec backend python ../seed_data/seed.py
# or, running locally against the compose Postgres:
cd backend && python ../seed_data/seed.py
```

Login with any of the seeded accounts — see the script's printed
output, or `seed_data/seed.py` directly. All use password
`CareFlow!2026`.

## Getting started — backend only (without Docker)

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit DB/Redis values for your machine
# Requires a running PostgreSQL and Redis instance — see .env.example
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

WebSocket/Celery pieces need a running Redis instance to actually
connect (Celery worker: `celery -A careflow_project worker -l info`;
beat: `celery -A careflow_project beat -l info`).

## Getting started — ML service

```bash
cd ml_service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python train.py                              # trains + saves both models
uvicorn app.main:app --reload --port 8001     # http://localhost:8001/docs
```

Set `ML_SERVICE_URL=http://localhost:8001` in the Django backend's
`.env` so `/predictions/*` can reach it.

## Getting started — frontend

```bash
cd frontend
npm install
cp .env.example .env   # defaults work with the dev proxy below
npm run dev             # http://localhost:5173
```

In dev, Vite proxies `/api/*` to `http://localhost:8000` (the Django
backend) — see `vite.config.js`. The WebSocket connects straight to
`ws://localhost:8000/ws/queue-updates/<department_id>/` (Django
Channels), bypassing the proxy. For production, build with `npm run
build` and set `VITE_API_BASE_URL` / `VITE_WS_BASE_URL` to your
deployed backend.

## Folder structure

```
backend/
  careflow_project/       # settings, urls, asgi/wsgi, celery.py, routing.py
  apps/
    users/                # custom User model, JWT auth, RBAC
    departments/          # Department model + live stats
    patients/             # Patient, QueueEvent, RBAC permissions, kiosk view, WS consumer
    staff/                # StaffShift model
    predictions/          # Prediction model, ML-service proxy views, Celery task
    alerts/                # Alert model + acknowledge flow
    analytics/             # trends, peak hours, bottlenecks, model accuracy
  requirements.txt
  .env.example
ml_service/
  app/
    main.py               # FastAPI app, CORS, model loading at startup
    schemas.py             # pydantic request/response models
    ml/
      wait_time.py         # loads + serves the wait-time model
      overcrowding.py       # loads + serves the overcrowding-risk model
      staffing.py            # rule-based recommendation engine
    routers/predictions.py  # all 4 endpoints
  data_generator.py         # synthetic data generators
  train.py                  # trains + evaluates + saves both models
  artifacts/                # wait_time_model.pkl, overcrowding_model.pkl, metrics.json (generated)
  requirements.txt
  .env.example
frontend/
  src/
    main.jsx, App.jsx        # providers, routing (14 pages, role-gated)
    lib/                     # api.js (JWT interceptors), useQueueSocket.js
    context/                 # Auth, Theme, Toast
    components/              # Sidebar, TopBar, Layout, StatCard, RiskGauge, ...
    pages/                   # Landing, Login, Dashboard, LiveQueueBoard, ...
  Dockerfile, nginx.conf
  .env.example
docker/
  docker-compose.yml         # all 7 services
  .env.example                # shared Postgres credentials
.github/workflows/
  ci-cd.yml                  # lint/test/build → GHCR, per service
seed_data/
  seed.py                    # departments, staff, patients, shifts, audit events
docs/
  architecture.md            # Mermaid system + sequence diagrams
  viva-qa-guide.md           # per-module Q&A for the presentation
```

## Deviations from the spec, with reasons (all documented inline too)

- **`socket.io-client` → native browser `WebSocket`**: Django Channels
  speaks plain WebSocket, not the socket.io protocol — using the
  spec'd library would have meant running a second, incompatible
  server. See `frontend/src/lib/useQueueSocket.js`.
- **Prophet → statsmodels (Holt-Winters/STL)** for overcrowding
  forecasting: lighter dependency, comparable trend quality on this
  data, documented in `ml_service/README.md`.
- **`GET /users/all` and `/users/:id`** were added in Phase 3 — not in
  the original route list, but required for the spec's own Admin Panel
  page to have anything to manage.

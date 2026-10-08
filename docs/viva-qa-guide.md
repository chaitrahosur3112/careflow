# CareFlow — Viva Q&A Guide

Organized by module. Each answer is written the way you'd actually say
it out loud — short, confident, and pointing at a specific file when
useful. Read the "why this and not X" answers closely; those are the
questions examiners actually probe on.

---

## 1. Overall architecture

**Q: Walk me through the system architecture in one minute.**
Three services. Django + DRF is the backend of record — it owns
Postgres, handles auth/RBAC, and serves the REST API. A separate
FastAPI microservice holds the ML models and is stateless — Django
proxies to it, never the frontend directly. Redis is shared
infrastructure: it's the Celery broker, the Django cache, and the
Channels layer for WebSocket pub/sub. React talks only to Django over
REST and one WebSocket connection for the live queue board. See
`docs/architecture.md` for the diagram.

**Q: Why split the ML service out instead of putting scikit-learn
inside Django?**
Different scaling and deployment needs — the ML service is
stateless and CPU-bound at inference time, so it can be scaled
independently of the request-handling Django pods. It also keeps the
Django codebase free of ML dependencies (scikit-learn, statsmodels,
pandas), and makes it possible to retrain/redeploy the model service
without touching the transactional backend at all.

**Q: Why does the frontend never call the ML service directly?**
Two reasons. First, RBAC and audit logging live in Django — every
prediction call needs to be authenticated and, for wait-time and
overcrowding-risk, logged to the `Prediction` table so the
model-accuracy dashboard has data. If the frontend called FastAPI
directly, we'd have to duplicate auth there. Second, it keeps FastAPI's
attack surface small: it doesn't need to know about users, JWTs, or
CORS-from-the-browser at all — only Django ever calls it, over an
internal network in Docker Compose.

---

## 2. Authentication & RBAC

**Q: How does login work end-to-end?**
POST `/auth/login` with email/password hits
`djangorestframework-simplejwt`'s `TokenObtainPairView`, which returns
an access token (15 min) and a refresh token (1 day). The frontend
stores both, attaches the access token as a Bearer header on every
request (`frontend/src/lib/api.js`), and on a 401 it silently calls
`/auth/refresh` once and retries the original request. If the refresh
itself fails, it clears tokens and redirects to `/login`.

**Q: Why 15-minute access tokens? Isn't that annoying?**
It's a deliberate security/UX tradeoff — short-lived access tokens
limit the blast radius if one leaks, and the silent refresh-and-retry
in `api.js` means the user never notices the token expired. Refresh
tokens rotate on every use and are blacklisted after rotation
(`SIMPLE_JWT` in `settings.py`), so a stolen refresh token is only
useful once.

**Q: How is role-based access control actually enforced — is it just
hiding buttons in the UI?**
No — hiding UI is UX, not security. Every protected endpoint has a
DRF permission class (`apps/patients/permissions.py`) checked
server-side: `IsAdmin`, `IsAdminOrNurse`, `IsAdminOrDoctorOrNurse`,
etc. The frontend's `RoleRoute.jsx` hides nav items and blocks
navigation for a better UX, but if a Nurse's browser sent a raw POST
to `/staff/all`, the backend would still reject it with 403 — I can
demo that with curl if asked.

**Q: What stops a Doctor in Cardiology from editing a patient in
Emergency?**
That's object-level, not just role-level, permission —
`IsSameDepartmentOrAdmin.has_object_permission` checks the requesting
user's `department` against the object's `department`, and several
list views (`PatientListView.get_queryset`) filter the queryset itself
to the user's own department unless they're Admin.

---

## 3. Data model & anonymization

**Q: The spec forbids storing patient medical records — how do you
enforce that, not just promise it?**
Structurally: the `Patient` model (`apps/patients/models.py`) has no
name, no diagnosis, no treatment field at all — only
`triage_level`, `department`, `status`, timestamps, and
`assigned_nurse`. There's nothing to leak because the schema doesn't
have the field. The primary key is a random UUID, not a
sequential/guessable ID.

**Q: How does the kiosk endpoint guarantee it never leaks patient
data?**
`KioskWaitTimesView` builds its response from `Department`
aggregates only (`bed_occupancy_pct`, `average_wait_time_minutes`) —
it never touches the `Patient` queryset directly. The serializer
(`KioskWaitTimeSerializer`) has exactly three fields:
`department_name`, `estimated_wait_minutes`, `load_level`. There's a
regression test for this —
`apps/patients/tests.py::KioskEndpointTests.test_kiosk_response_never_contains_patient_fields`
— that asserts the response keys are exactly that set.

**Q: Why UUIDs instead of auto-incrementing integer IDs everywhere?**
Sequential IDs leak information (total patient count, growth rate)
and are trivially enumerable — `/patients/1`, `/patients/2`, ... An
attacker (or a curious person) could infer daily patient volume from
ID gaps alone. UUIDs close that off.

---

## 4. Real-time updates (WebSocket)

**Q: Why Django Channels instead of Socket.IO, which the original
spec named?**
Channels is Django-native — it reuses the same ASGI app, the same
auth middleware stack, and doesn't require running a separate Node
process alongside Django. Socket.IO needs a compatible server (usually
Node or `python-socketio`), which would mean either a second runtime
or losing the tight Django integration. The frontend uses the plain
browser `WebSocket` API (`frontend/src/lib/useQueueSocket.js`) to talk
to it — no client library needed either.

**Q: What actually gets sent over the WebSocket — please tell me it's
not patient data.**
It's not. The consumer (`apps/patients/consumers.py`) sends exactly
`{"type": "queue_update", "department_id": "..."}` — a signal to
refetch, nothing else. The frontend receives that and calls the normal
authenticated REST endpoint (`/departments/:id/queue`) to get the
actual data. This means the live board is only ever as fresh as the
last REST call, but it also means every actual data read goes through
the same RBAC path as a normal page load — there's no separate,
weaker-authenticated data channel to worry about.

**Q: How does a client subscribe to only their department's updates?**
The WebSocket URL is `/ws/queue-updates/<department_id>/`, and the
consumer joins a Channels group named `queue_<department_id>` on
connect. When a patient's status changes in that department,
`_broadcast_queue_update()` in `apps/patients/views.py` sends to that
specific group — other departments' connected clients never see it.

---

## 5. Background jobs (Celery)

**Q: What does Celery actually do here — why not just compute
everything on each request?**
One recurring task, `recompute_all_predictions`
(`apps/predictions/tasks.py`), runs every 5 minutes via Celery Beat
and checks every active department's bed occupancy against the
amber/red thresholds, raising `Alert` rows as needed, and separately
flags any patient who's been waiting past the long-wait threshold.
The point is that overcrowding shouldn't require someone to be
actively polling `/predictions/overcrowding-risk` — a department can
quietly cross 95% occupancy on a quiet night shift and still get
flagged.

**Q: Why not put this logic in a Django management command run by
cron instead of Celery?**
Celery is already required for anything async-and-periodic done the
"correct" way in a Django app of this shape, and it gives us retry
semantics, monitoring, and — more concretely for this project — Redis
was already a dependency for Channels, so Celery reuses the same
broker rather than adding a new moving part.

---

## 6. Machine learning

**Q: Why Gradient Boosting for wait-time prediction instead of a
neural net?**
The feature set is small and mostly tabular/categorical (queue
length, staff on duty, triage level, time of day, day of week) —
gradient-boosted trees are the standard strong baseline for tabular
regression at this scale, they don't need feature scaling, and they
give feature-importance for free, which matters for explaining the
prediction to hospital staff. A neural net would need far more data
to beat it here and would be a black box for no benefit.

**Q: The spec mentioned Prophet for overcrowding forecasting — did
you use it?**
No — `statsmodels` (Holt-Winters / STL-style exponential smoothing)
instead, documented in `ml_service/README.md` and the root README. On
synthetic, fairly smooth demo data, Prophet's extra machinery
(changepoint detection, holiday effects) is overkill and adds a heavy
dependency; Holt-Winters gets a comparable trend forecast with a much
lighter footprint, and the output is blended with the *current* live
occupancy reading so a department that's already critical is never
masked by a smoothed-over forecast.

**Q: What are your model's actual validation numbers, and are you
sure they're not overfit on synthetic data?**
Wait-time model: MAE 3.41 minutes, RMSE 4.30, R² 0.992 on a held-out
test split. Overcrowding-risk model: MAE 2.82, RMSE 3.59, R² 0.922.
These are good because the synthetic data generator
(`ml_service/data_generator.py`) is built from clean formulas plus
noise — real hospital data would be noisier and the model would need
retraining on it before those numbers meant anything clinically. The
`/model/metrics` endpoint and the Admin dashboard show these numbers
directly rather than hiding them, precisely so this caveat is visible.

**Q: Is the staffing recommendation itself a machine-learned model?**
No — deliberately not. It's rule-based
(`ml_service/app/ml/staffing.py`): explainable thresholds tied to the
same amber/red cutoffs used for alerts, with a hard ceiling on how
many staff it will ever recommend adding in one call. A hospital
administrator needs to be able to see *why* a recommendation was made,
and a black-box model recommending staffing changes is a much bigger
trust and liability problem than a black-box wait-time estimate.

**Q: You mentioned catching a bug — what was it?**
`current_load` in the staffing endpoint was ambiguous — I passed it a
percentage in a manual test and the math (which divides load by a
target-patients-per-staff ratio) produced "add 18 nurses," which is
absurd for one shift. I fixed it by documenting the field as a patient
*count* in both the Pydantic schema and the Django serializer, and
added a hard cap (`MAX_RECOMMENDED_ADDITION = 5`) plus a regression
test (`ml_service/tests/test_main.py::test_staffing_recommendation_never_suggests_unrealistic_addition`)
so it can't regress.

---

## 7. Security

**Q: Where are secrets stored — did you hardcode anything?**
Nowhere in code. Every secret (DB password, Django `SECRET_KEY`,
Redis URL) is read from environment variables via `python-decouple`
in `settings.py`, with `.env.example` files documenting what's needed
without containing real values. `.env` itself is gitignored.

**Q: What's rate-limited, and why?**
Login (`/auth/login`) and the public kiosk endpoint both have DRF
`ScopedRateThrottle` limits (`auth`: 10/min, `kiosk`: 60/min) — login
to slow brute-force credential guessing, kiosk because it's the one
endpoint with no auth at all and needs its own abuse protection.

**Q: How is every action attributable — is there an audit trail?**
Yes — `QueueEvent` (`apps/patients/models.py`) records every intake,
status change, and discharge with `performed_by` and a timestamp, and
is never edited or deleted, only appended to. `Alert.acknowledged_by`
similarly tracks who cleared an alert and when.

---

## 8. Deployment & scalability

**Q: How would you actually run this?**
`docker/docker-compose.yml` brings up all seven services locally —
Postgres, Redis, the ML service, Django (via Daphne, since ASGI is
needed for WebSockets), a Celery worker, Celery beat, and the React
build served by Nginx, which also reverse-proxies `/api/` and `/ws/`
to Django. In production the same images would run on AWS ECS Fargate
or Kubernetes, with managed Postgres (RDS) and Redis (ElastiCache)
instead of the containerized versions.

**Q: What's the CI/CD pipeline actually check before deploying?**
`.github/workflows/ci-cd.yml`: lint + Django system check + migration
check + the real test suite (`manage.py test`) for the backend, lint +
pytest for the ML service, and a production build for the frontend —
all three run in parallel, and only if all three pass does it build
and push Docker images to GHCR. The final deploy step is a documented
placeholder, not a real deploy target, since there's no live AWS
account behind this project.

**Q: How would this scale to a real multi-hospital deployment?**
The department model already supports multiple departments per
"hospital"; making it properly multi-tenant would mean adding a
`Hospital` model that `Department` belongs to, scoping every queryset
by it, and likely moving the ML service to serve per-hospital models
if hospitals' patient-flow patterns differ enough to need separate
training data. The current schema doesn't block that — it's an
additive change, not a rewrite.

---

## 9. Honest limitations (say these before they're asked)

- All data is synthetic — no real hospital validated this system's
  predictions against ground truth.
- Not HIPAA-compliant as-is — the disclaimer in the root README is
  not boilerplate, it's load-bearing.
- The overcrowding model's "risk score" is a heuristic composition of
  a smoothed forecast and live occupancy, not a peer-reviewed clinical
  scoring system.
- No end-to-end (Cypress/Playwright) tests — only backend unit tests
  and ML service endpoint tests exist; the frontend has none.

# CareFlow — Render Production Deployment Guide

This guide walks you through deploying the complete **CareFlow** application to [Render](https://render.com), making all services publicly accessible via HTTPS.

---

## Architecture on Render

```
                  ┌───────────────────────────────┐
                  │       Client Browser          │
                  └──────┬─────────────────┬──────┘
                         │ HTTPS           │ WSS
                         ▼                 ▼
          ┌──────────────────────────┐    │
          │   careflow-frontend      │    │
          │   (Render Static Site)   │    │
          └──────────────┬───────────┘    │
                         │ HTTPS REST     │
                         ▼                ▼
                 ┌─────────────────────────────────┐
                 │        careflow-backend         │
                 │   (Daphne ASGI Web Service)     │
                 └──────┬─────────────┬────────────┘
                        │             │ HTTP Proxy
           PostgreSQL   │             ▼
       ┌────────────────┴┐    ┌──────────────────┐
       │   careflow-db   │    │   careflow-ml    │
       │  (Postgres DB)  │    │ (FastAPI Service)│
       └─────────────────┘    └──────────────────┘
```

---

## Option 1: One-Click Automated Deployment (Render Blueprint)

The repository includes a ready-to-use [`render.yaml`](../render.yaml) blueprint.

1. Log into your [Render Dashboard](https://dashboard.render.com).
2. Click **New +** in the top navigation bar and select **Blueprint**.
3. Connect your GitHub account and choose the repository: **`chaitrahosur3112/careflow`**.
4. Render will parse `render.yaml` and display the four resources to be created:
   - `careflow-db` (PostgreSQL Database)
   - `careflow-ml` (FastAPI Web Service)
   - `careflow-backend` (Django Daphne ASGI Web Service)
   - `careflow-frontend` (React/Vite Static Site)
5. Click **Apply**.
6. Render will automatically provision the database, build the ML service, run backend migrations and static collection, and compile the frontend production bundle.

---

## Option 2: Step-by-Step Manual Deployment

If you prefer configuring each service individually in the Render Dashboard, follow these steps in order:

### Step 1: Create the PostgreSQL Database
1. Go to **New +** -> **PostgreSQL**.
2. Set the following fields:
   - **Name:** `careflow-db`
   - **Database:** `careflow`
   - **User:** `careflow_user`
   - **Region:** Choose the region closest to you (e.g., Oregon or Frankfurt). Note this region, as all services should be in the same region.
   - **Plan:** `Free`
3. Click **Create Database**.
4. Once created, copy the **Internal Database URL** (e.g., `postgres://careflow_user:...@dpg-.../careflow`).

---

### Step 2: Deploy the ML Microservice (`careflow-ml`)
1. Go to **New +** -> **Web Service**.
2. Connect repository **`chaitrahosur3112/careflow`**.
3. Configure the service:
   - **Name:** `careflow-ml`
   - **Region:** Same as your database.
   - **Branch:** `main`
   - **Root Directory:** `ml_service`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** `Free`
4. Expand **Advanced** and set:
   - **Health Check Path:** `/health`
   - **Environment Variables:**
     - `PYTHON_VERSION`: `3.12.9`
5. Click **Create Web Service**.
6. When deployment finishes, copy your ML service URL:  
   `https://careflow-ml.onrender.com`

---

### Step 3: Deploy the Django Backend (`careflow-backend`)
1. Go to **New +** -> **Web Service**.
2. Connect repository **`chaitrahosur3112/careflow`**.
3. Configure the service:
   - **Name:** `careflow-backend`
   - **Region:** Same as database and ML service.
   - **Branch:** `main`
   - **Root Directory:** `backend`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Pre-Deploy Command:** `python manage.py migrate --noinput`
   - **Start Command:** `daphne -b 0.0.0.0 -p $PORT careflow_project.asgi:application`
   - **Plan:** `Free`
4. Expand **Advanced** and set:
   - **Health Check Path:** `/kiosk/wait-times`
   - **Environment Variables:**
     | Key | Value / Source |
     | :--- | :--- |
     | `PYTHON_VERSION` | `3.12.9` |
     | `DJANGO_DEBUG` | `False` |
     | `DJANGO_SECRET_KEY` | *(Click "Generate" or provide a secure 50-char random string)* |
     | `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,.onrender.com` |
     | `DATABASE_URL` | *(Paste Internal Database URL from Step 1)* |
     | `ML_SERVICE_URL` | `https://careflow-ml.onrender.com` *(from Step 2)* |
     | `CORS_ALLOWED_ORIGINS` | `https://careflow-frontend.onrender.com,http://localhost:5173` |
     | `CSRF_TRUSTED_ORIGINS` | `https://*.onrender.com,http://localhost:5173` |
     | `SECURE_SSL_REDIRECT` | `False` |
     | `REDIS_URL` | *(Optional: see Redis section below)* |
5. Click **Create Web Service**.
6. When deployment finishes, copy your Backend URL:  
   `https://careflow-backend.onrender.com`

---

### Step 4: Deploy the React Frontend (`careflow-frontend`)
1. Go to **New +** -> **Static Site**.
2. Connect repository **`chaitrahosur3112/careflow`**.
3. Configure the site:
   - **Name:** `careflow-frontend`
   - **Branch:** `main`
   - **Root Directory:** `frontend`
   - **Build Command:** `npm install && npm run build`
   - **Publish Directory:** `dist`
4. In **Redirects/Rewrites**:
   - Add a rewrite rule for single-page application routing:
     - **Type:** `Rewrite`
     - **Source:** `/*`
     - **Destination:** `/index.html`
5. In **Environment Variables**:
   | Key | Value |
   | :--- | :--- |
   | `VITE_API_BASE_URL` | `https://careflow-backend.onrender.com` |
   | `VITE_WS_BASE_URL` | `wss://careflow-backend.onrender.com` |
6. Click **Create Static Site**.
7. When deployment completes, your site will be live at:  
   `https://careflow-frontend.onrender.com`

---

## Post-Deployment Procedures

### 1. Creating an Administrator Account
To create your initial superuser safely without storing passwords in repository code:

1. In Render Dashboard, click on your **`careflow-backend`** service.
2. Click the **Shell** tab on the left menu (opens a terminal inside the container).
3. Run the interactive Django command:
   ```bash
   python manage.py createsuperuser
   ```
4. Enter your admin email, username, and secure password when prompted.
5. You can now log into CareFlow as an Admin!

---

### 2. (Optional) Populating Demo Synthetic Data
If you are deploying for a demonstration, thesis defense, or evaluation and want synthetic hospital data (Departments, Staff, Patients, Predictions, Alerts):

1. Open the **Shell** tab on **`careflow-backend`**.
2. Run the safe, idempotent command:
   ```bash
   python manage.py seed_demo_data
   ```
3. Default demo logins created:
   - **Admin:** `admin.seed@careflow.demo` / `CareFlow!2026`
   - **Doctor:** `vikram.seed@careflow.demo` / `CareFlow!2026`
   - **Nurse:** `divya.seed@careflow.demo` / `CareFlow!2026`
   - **Hospital Admin:** `hospitaladmin.seed@careflow.demo` / `CareFlow!2026`

*Note: Demo data is purely synthetic with no real patient information and will never wipe custom patient records.*

---

## Free-Tier Considerations & Redis Setup

### 1. Inactivity Spin-Down
Render's free-tier Web Services spin down after 15 minutes of inactivity. When a request arrives, the service takes ~30–50 seconds to wake up (cold start).
- The frontend features reconnect logic with exponential backoff on both REST API and WebSocket connections.
- The Kiosk endpoint (`/kiosk/wait-times`) can be used as an uptime monitor target (e.g., with UptimeRobot or Cron-job.org) to keep instances warm if desired.

### 2. WebSockets & Channels
- **Single-instance (Default):** CareFlow includes an automatic in-memory channel layer fallback (`InMemoryChannelLayer`). WebSocket notifications for the Live Queue work on Render out of the box without Redis.
- **Multi-worker / Distributed Redis (Recommended for Production Scale):**
  - Sign up for a free cloud Redis instance on [Upstash](https://upstash.com) (free 10,000 commands/day) or create a Render Redis instance.
  - Set the `REDIS_URL` environment variable on `careflow-backend`:
    ```
    REDIS_URL=rediss://default:your-password@your-endpoint.upstash.io:6379
    ```
  - Django Channels will automatically use `RedisChannelLayer`, and rate-limiting will use `RedisCache`.

---

## Health Check Endpoints

| Service | Protocol | Endpoint | Expected Output |
| :--- | :--- | :--- | :--- |
| **ML Microservice** | HTTP | `GET /health` | `{"status": "healthy"}` |
| **ML Model Metrics** | HTTP | `GET /model/metrics` | Model performance statistics |
| **Backend Kiosk** | HTTP | `GET /kiosk/wait-times` | `200 OK` (JSON wait times) |
| **Backend Admin** | HTTP | `GET /admin/login/` | `200 OK` (HTML Django login) |
| **Frontend** | HTTPS | `GET /` | `200 OK` (Landing page) |

---

## Troubleshooting

### 1. CORS Errors (`Cross-Origin Request Blocked`)
- **Symptom:** Browser console shows `Access to XMLHttpRequest has been blocked by CORS policy`.
- **Fix:** In `careflow-backend` environment variables, verify `CORS_ALLOWED_ORIGINS` contains the exact URL of your frontend (e.g., `https://careflow-frontend.onrender.com`) without a trailing slash.

### 2. Single Page App 404 on Refresh
- **Symptom:** Refreshing `https://careflow-frontend.onrender.com/dashboard` returns a 404 Not Found error.
- **Fix:** On your static site settings in Render, add a Rewrite rule:  
  Source: `/*` -> Destination: `/index.html`.

### 3. Database Connection Timeout
- **Symptom:** Backend fails with `OperationalError: could not translate host name...`
- **Fix:** Ensure you used the **Internal Database URL** for `DATABASE_URL` (which uses the internal network name and avoids egress charges), and that both the database and web services are in the **same Render region**.

### 4. Predictions Return HTTP 500
- **Symptom:** Requesting wait-time or overcrowding predictions fails.
- **Fix:** Check `ML_SERVICE_URL` in `careflow-backend` environment variables. It must point to your deployed ML service (e.g., `https://careflow-ml.onrender.com`).

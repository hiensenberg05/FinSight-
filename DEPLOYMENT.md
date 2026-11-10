# 🚀 FinSight Deployment & Production Operations Guide

This guide covers deploying **FinSight** to production using **Render** and running locally or on any server using **Docker Compose**.

---

## 📑 Table of Contents
1. [Stack Architecture](#stack-architecture)
2. [Local & Server Deployment with Docker Compose](#local--server-deployment-with-docker-compose)
3. [Deploying to Render (Recommended Cloud Platform)](#deploying-to-render)
   - [Method 1: One-Click Render Blueprint (render.yaml)](#method-1-one-click-render-blueprint)
   - [Method 2: Manual Dashboard Setup (Step-by-Step)](#method-2-manual-dashboard-setup)
4. [Environment Variables Reference](#environment-variables-reference)
5. [Post-Deployment Health & Verification Checklist](#post-deployment-verification)
6. [Troubleshooting & FAQs](#troubleshooting--faqs)

---

## 🏛️ Stack Architecture

```mermaid
flowchart LR
    Browser["User Browser / Client"]
    
    subgraph Cloud ["Render Cloud Infrastructure"]
        Frontend["finsight-web\n(React 19 + Vite Static Site / CDN)"]
        Backend["finsight-api\n(FastAPI + Playwright + Python 3.11)"]
        Database[("finsight-db\n(Managed PostgreSQL 16)")]
    end

    subgraph External ["External Services"]
        Gnani["Gnani.ai Vachana & Timbre"]
        Groq["Groq Llama-3 / GPT-OSS"]
        Slack["Slack Bot & Webhooks"]
    end

    Browser -- HTTPS (Static UI) --> Frontend
    Browser -- HTTPS / REST (/api/v1) --> Backend
    Browser -- WSS Full-Duplex (/ws/voice) --> Backend
    Backend -- AsyncPG SQL --> Database
    Backend -- Audio PCM Stream --> Gnani
    Backend -- Reasoning Queries --> Groq
    Backend -- Interactive Block Kit --> Slack
```

FinSight is composed of three interconnected services:
1. **Database**: PostgreSQL 16 relational database with deterministic ACID transactions.
2. **Backend**: FastAPI ASGI server with WebSockets, Playwright headless Chromium for real-time DOM forensics, and ReAct agentic orchestration.
3. **Frontend**: React 19 Single-Page Application (SPA) with Three.js 3D sound orb, Tailwind CSS, and Web Audio API stream processing.

---

## 🐳 Local & Server Deployment with Docker Compose

Deploy the entire production stack locally or on any Linux VPS with one command:

### 1. Configure Environment File
Ensure you have a `.env` file in the root directory:

```bash
cp .env.example .env
```

Populate the required credentials:
```env
# AI Providers
GNANI_API_KEY=your_gnani_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Slack Sentinel
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../...
SLACK_BOT_TOKEN=xoxb-...
SLACK_USER_TOKEN=xoxp-...
SLACK_CHANNEL_ID=C09M5ETUMPF
SLACK_CHANNEL_NAME=#engineering-inventory-tracker
```

### 2. Build and Start Containers
```bash
docker compose up -d --build
```

Docker Compose will start:
- `finsight-postgres` on `localhost:5432`
- `finsight-backend` on `localhost:8000` (auto-runs migrations & Aarav Mehta seed data)
- `finsight-frontend` on `localhost:80` (and `localhost:5173`) with Nginx reverse proxy

### 3. Verify Containers
```bash
docker compose ps
```

Access the services:
- **Web Dashboard**: [http://localhost:80](http://localhost:80) or [http://localhost:5173](http://localhost:5173)
- **Backend API & Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

### 4. Stop Containers
```bash
docker compose down
# Or to wipe database volume:
docker compose down -v
```

---

## ☁️ Deploying to Render

Render is the recommended hosting platform for FinSight because it natively supports:
- **Full-Duplex WebSockets** (wss://) on all endpoints without complex ingress configuration.
- **Docker Runtimes** with headless Chromium / Playwright sandbox execution.
- **Managed PostgreSQL** with automated backups and private networking.
- **Fast Global CDN** for React static assets.

You can deploy using either **Method 1 (render.yaml Blueprint)** or **Method 2 (Manual Dashboard)**.

---

### Method 1: One-Click Render Blueprint (`render.yaml`)

This repository includes a production-ready `render.yaml` specification file.

1. **Push your code to GitHub**:
   Ensure all changes are pushed to your remote Git repository (`main` branch).

2. **Open Render Dashboard**:
   Go to [https://dashboard.render.com](https://dashboard.render.com).

3. **Create New Blueprint**:
   - Click the **New +** button in the top right.
   - Select **Blueprint**.
   - Connect your GitHub repository (`FinSight-`).
   - Render will detect `render.yaml` and parse all 3 resources:
     - `finsight-db` (PostgreSQL)
     - `finsight-api` (Docker Web Service)
     - `finsight-web` (Static Site)

4. **Supply Secret Environment Variables**:
   In the Blueprint setup screen, enter the values for:
   - `GNANI_API_KEY`
   - `GROQ_API_KEY`
   - `SLACK_WEBHOOK_URL`
   - `SLACK_BOT_TOKEN`
   - `SLACK_USER_TOKEN`

5. **Click Apply**:
   Render will automatically provision the database, build the backend Docker container, compile the React frontend, and link all URLs!

---

### Method 2: Manual Dashboard Setup (Step-by-Step)

If you prefer configuring each service manually via the Render UI:

#### Step 1: Create Managed PostgreSQL Database
1. In Render Dashboard, click **New +** $\rightarrow$ **PostgreSQL**.
2. **Name**: `finsight-db`
3. **Database**: `finsight`
4. **User**: `finsight_user`
5. **Region**: Choose the closest region (e.g., `Oregon` or `Singapore`).
6. **Plan**: `Free` or `Starter`.
7. Click **Create Database**.
8. Once provisioned, copy the **Internal Database URL** (e.g., `postgres://finsight_user:...@dpg-...:5432/finsight`).

---

#### Step 2: Deploy Backend Web Service (FastAPI + Playwright)
1. In Render Dashboard, click **New +** $\rightarrow$ **Web Service**.
2. Connect your `FinSight-` GitHub repository.
3. Configure settings:
   - **Name**: `finsight-api`
   - **Region**: Same as database (e.g., `Oregon`).
   - **Branch**: `main`
   - **Runtime**: **Docker**
   - **Dockerfile Path**: `./backend/Dockerfile` (or root `./Dockerfile`)
   - **Docker Context**: `.`
   - **Instance Type**: `Starter` ($7/mo recommended for Playwright headless browser; `Free` works for test/demo workloads).
4. **Advanced Settings**:
   - **Health Check Path**: `/health`
5. **Environment Variables**: Add the following:

| Key | Value | Note |
|---|---|---|
| `PORT` | `10000` | Render injects this automatically |
| `APP_ENV` | `production` | Production mode |
| `DEBUG` | `false` | Disable debug logs |
| `DATABASE_URL` | *Paste Internal Database URL* | FinSight auto-converts `postgres://` to `postgresql+asyncpg://` |
| `GNANI_API_KEY` | `your_gnani_token` | Vachana STT & Timbre TTS |
| `GROQ_API_KEY` | `your_groq_key` | Fast ReAct LLM Reasoning |
| `SLACK_WEBHOOK_URL` | `https://hooks.slack.com/...` | Slack Sentinel notifications |
| `SLACK_BOT_TOKEN` | `xoxb-...` | Slack Bot authorization |
| `SLACK_USER_TOKEN` | `xoxp-...` | Optional user authorization |
| `SLACK_CHANNEL_ID` | `C09M5ETUMPF` | Target channel ID |
| `SLACK_CHANNEL_NAME` | `#engineering-inventory-tracker` | Channel name |
| `SECRET_KEY` | *(Click "Generate")* | Cryptographic JWT signing key |

6. Click **Create Web Service**.
7. Note down your backend URL once live:
   `https://finsight-api.onrender.com`

---

#### Step 3: Deploy Frontend Static Site (React 19 + Vite)
1. In Render Dashboard, click **New +** $\rightarrow$ **Static Site**.
2. Connect your `FinSight-` GitHub repository.
3. Configure settings:
   - **Name**: `finsight-web`
   - **Branch**: `main`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`
4. **Environment Variables**: Add the following:

| Key | Value |
|---|---|
| `VITE_API_BASE_URL` | `https://finsight-api.onrender.com/api/v1` |
| `VITE_WS_URL` | `wss://finsight-api.onrender.com/ws/voice` |

*(Replace `finsight-api.onrender.com` with your actual Render backend URL)*

5. **Redirects/Rewrites (Important for Single-Page Apps)**:
   - Navigate to the **Redirects/Rewrites** tab on the static site dashboard.
   - Click **Add Rule**:
     - **Type**: `Rewrite`
     - **Source**: `/*`
     - **Destination**: `/index.html`
   *(This ensures that direct navigation or refreshing sub-pages routes cleanly to the React router).*

6. Click **Create Static Site**.

---

## 🔑 Environment Variables Reference

| Variable | Required | Description | Example |
|---|---|---|---|
| `PORT` | Yes (Cloud) | Port on which FastAPI binds | `8000` or `10000` |
| `DATABASE_URL` | Yes | SQLite or PostgreSQL connection string | `postgresql+asyncpg://user:pass@host/db` |
| `GNANI_API_KEY` | Yes | Speech-to-Text & Text-to-Speech token | `5204739a-ca57-...` |
| `GROQ_API_KEY` | Yes | High-speed LLM inference | `gsk_...` |
| `SLACK_WEBHOOK_URL`| Yes | Incoming webhook for alerts | `https://hooks.slack.com/services/...` |
| `SLACK_BOT_TOKEN` | Yes | Bot token for interactive blocks | `xoxb-...` |
| `SLACK_CHANNEL_ID` | Yes | Channel for automated financial alerts | `C09M5ETUMPF` |
| `SECRET_KEY` | Yes | Secret key for JWT hashing | 32+ character random string |

---

## ✅ Post-Deployment Verification

Once deployed, run through this verification checklist:

1. **Health Check Endpoint**:
   Open `https://finsight-api.onrender.com/health` in your browser.
   Expected response:
   ```json
   {"status":"healthy","database":"connected"}
   ```

2. **Interactive Swagger API Docs**:
   Open `https://finsight-api.onrender.com/docs`.
   Verify all endpoints (`/api/v1/analytics/health`, `/api/v1/bills`, `/api/v1/voice/query`, etc.) are visible and responding.

3. **Frontend Dashboard & 3D Sound Orb**:
   Open `https://finsight-web.onrender.com`.
   - Verify green status indicator: **"14ms Gateway Connected"**.
   - Verify Financial Health Gauge displays real score (e.g., `27 / 100`).
   - Verify What-If Simulator slider calculates dynamic savings run-rates.

4. **Bi-Directional Voice Gateway**:
   - Click the 3D Sound Orb and speak:
     > *"Show me my dining spending and check the Swiggy receipt."*
   - Verify that Playwright headless browser runs forensics and returns the itemized receipt.
   - Confirm affirmative follow-up:
     > *"Send alert to Slack."*
   - Check Slack channel `#engineering-inventory-tracker` for the real-time Block Kit card.

---

## 🛠️ Troubleshooting & FAQs

### Q: Why does Render PostgreSQL URL fail with SQLAlchemy?
**Answer**: Render gives PostgreSQL URLs starting with `postgres://` or `postgresql://`. Standard SQLAlchemy async engines require `postgresql+asyncpg://`. FinSight includes an automatic URL normalizer in [`backend/app/db/session.py`](backend/app/db/session.py) that transparently rewrites this and removes `?sslmode=require` so it works out-of-the-box on Render.

### Q: Does Render free tier support WebSockets?
**Answer**: **Yes!** Render natively supports WebSockets across all plans (Free, Starter, Standard). The connection string is standard `wss://<your-service>.onrender.com/ws/voice`.

### Q: Does Playwright work on Render?
**Answer**: Yes, when using the provided Docker container (`backend/Dockerfile`), which installs all necessary Linux shared libraries (`libnss3`, `libasound2`, `libgbm1`, etc.) and the Chromium browser binary.

### Q: What if the Render free instance spins down?
**Answer**: Free instances on Render spin down after 15 minutes of inactivity. The first request may take 30–45 seconds to spin up. For instant sub-second voice latency during live hackathon demos, using Render's **Starter** instance ($7/mo) keeps the service warm 24/7.

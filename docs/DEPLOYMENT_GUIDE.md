# FinAgent — Cloud Deployment Guide (Supabase + Vercel + Backend)

This guide walks you through fully deploying **FinAgent** to the cloud using **Supabase** (PostgreSQL + pgvector) and **Vercel** (Next.js Frontend).

---

## Architecture at a Glance

```
                  ┌───────────────────────────────┐
                  │      Next.js Frontend         │
                  │      (Deployed on Vercel)     │
                  └───────────────┬───────────────┘
                                  │ HTTPS
                                  ▼
                  ┌───────────────────────────────┐
                  │      FastAPI + LangGraph      │
                  │ (Render / Railway / Fly.io)   │
                  └──────┬─────────────────┬──────┘
                         │                 │
                         ▼                 ▼
          ┌───────────────────────┐ ┌─────────────┐
          │  Supabase PostgreSQL  │ │ OpenAI API  │
          │   (with pgvector)     │ └─────────────┘
          └───────────────────────┘
```

---

## 1. Step 1: Set up Supabase Database

1. Go to [https://supabase.com](https://supabase.com) and create a free project (e.g. `finagent`).
2. **Enable pgvector**:
   - In your Supabase Dashboard, click on **SQL Editor** on the left.
   - Run:
     ```sql
     CREATE EXTENSION IF NOT EXISTS vector;
     ```
3. **Execute the Database Schema**:
   - Open [`database/schema.sql`](file:///Users/uakash/Desktop/SampleProject/database/schema.sql) from this project.
   - Copy the entire SQL content, paste it into the Supabase SQL Editor, and click **Run**.
   - This creates all 8 tables (`users`, `user_preferences`, `expenses`, `budgets`, `alerts`, `agent_events`, `recurring_expenses`, `monthly_reports`) with indexes and vector embeddings.
4. **Obtain your Supabase Database URI**:
   - Go to **Project Settings** $\to$ **Database** $\to$ **Connection string**.
   - Select **URI** (Direct connection on port `5432` or Transaction Pooler on port `6543`).
   - The connection string will look like:
     ```
     postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
     ```
   - Make sure to replace `[YOUR-PASSWORD]` with your database password.

---

## 2. Step 2: Deploy the Backend (FastAPI + LangGraph)

You can host the Python backend on **Render**, **Railway**, **Fly.io**, or **AWS**:

### Recommended Option: Deploy on Render (Free & 1-Click)
1. Push this project to GitHub.
2. Go to [https://render.com](https://render.com) and click **New +** $\to$ **Web Service**.
3. Select your repository.
4. Configure:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. **Add Backend Environment Variables** (Under Environment tab):

| Variable Name | Value | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://postgres.[REF]:[PASS]@...:6543/postgres` | Your Supabase PostgreSQL connection string |
| `OPENAI_API_KEY` | `sk-proj-...` | Your OpenAI API key (optional: uses smart local reasoning fallback if empty) |
| `SECRET_KEY` | `your-secure-random-32-char-jwt-secret` | JWT encryption secret |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `AGENT_CONFIDENCE_THRESHOLD` | `0.75` | Confidence trigger threshold for clarifications |
| `ANOMALY_SENSITIVITY` | `0.70` | Composite sensitivity for 3-layer anomaly detector |

6. Once deployed, Render provides your backend URL: e.g. `https://finagent-api.onrender.com`.

---

## 3. Step 3: Deploy the Frontend to Vercel

1. Go to [https://vercel.com](https://vercel.com) and click **Add New...** $\to$ **Project**.
2. Select your GitHub repository.
3. In the project configuration:
   - **Root Directory**: Select `frontend` (or leave default if importing repository with `frontend/`).
   - **Framework Preset**: Next.js (automatically detected).
4. **Add Vercel Environment Variables**:

| Variable Name | Value | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://finagent-api.onrender.com/api` | Your deployed backend URL from Step 2 |
| `BACKEND_INTERNAL_URL` | `https://finagent-api.onrender.com` | Internal proxy target for Next.js rewrites |

5. Click **Deploy**. Vercel will build and deploy your application in under a minute!

---

## 4. Where to Put API Keys & Environment Variables Summary

### In Local Development (`.env` file in root):
```bash
# Database: SQLite locally, or Supabase PostgreSQL URI
DATABASE_URL="sqlite:///./finagent.db"
# Or for Supabase:
# DATABASE_URL="postgresql+psycopg2://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"

# OpenAI API Key (Agent falls back to intelligent local engine if left empty)
OPENAI_API_KEY="sk-proj-your-openai-api-key"

# JWT Secret
SECRET_KEY="supersecretfinagentjwtkeypleasechangethisinproduction"

# Agent Thresholds
AGENT_CONFIDENCE_THRESHOLD=0.75
ANOMALY_SENSITIVITY=0.70
```

### In Frontend Local Development (`frontend/.env.local`):
```bash
# Points to local backend or deployed cloud backend
NEXT_PUBLIC_API_URL="http://localhost:8000/api"
```

### In Cloud Production:
- **Supabase Dashboard**: Execute `database/schema.sql` in SQL Editor.
- **Render / Cloud Host Dashboard**: Set `DATABASE_URL`, `OPENAI_API_KEY`, `SECRET_KEY`.
- **Vercel Dashboard**: Set `NEXT_PUBLIC_API_URL`.

---

## 5. Verifying the Deployment

1. Visit your Vercel URL (e.g. `https://finagent.vercel.app`).
2. The demo credentials work out of the box:
   - **Email**: `demo@finagent.ai`
   - **Password**: `finagent123`
3. Try the demo scenarios:
   - Add `"₹4,500 — Restaurant — Today"` $\to$ Observe 3-layer anomaly scoring & proactive alert.
   - Add `"Paid ₹2,500 to Rahul"` $\to$ Observe low-confidence clarification request with interactive category chips.
   - Ask `"Am I spending too much on food?"` $\to$ Observe autonomous multi-tool reasoning and trend breakdown.

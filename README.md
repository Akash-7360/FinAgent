# FinAgent — Agentic Personal Expense Intelligence

**FinAgent** is a production-quality, autonomous financial intelligence platform powered by **LangGraph**, **FastAPI**, **Next.js**, **Tailwind CSS**, and a **3-Layer Anomaly Detection Engine** (Rules, Statistical Z-score/IQR, and Isolation Forest ML).

Unlike typical CRUD expense apps, FinAgent perceives user transactions, checks categorization confidence, queries personalized memory, assesses budget velocity, detects subtle or large-scale spending anomalies, reasons about next actions, and autonomously generates proactive alerts.

---

## Key Features

1. **Autonomous LangGraph Orchestrator**:
   - Multi-step reasoning: Perceive -> Confidence Check -> Plan Tools -> Execute Tools -> Observe -> Synthesize -> Audit.
   - 14 Dynamic Tools: `add_expense`, `get_expense_history`, `get_category_spending`, `get_monthly_spending`, `get_merchant_history`, `search_similar_transactions`, `check_budget`, `create_budget`, `update_budget`, `detect_anomaly`, `calculate_spending_trend`, `generate_monthly_report`, `create_alert`, `get_user_preferences`.
2. **Confidence-Aware Categorization**:
   - Identifies ambiguous transactions (e.g. *"Paid ₹2,500 to Rahul"*).
   - Prompts the user for clarification instead of blindly guessing.
3. **3-Layer Hybrid Anomaly Detection**:
   - **Layer 1**: Heuristic rule constraints (e.g. >3x category average, sudden dining spikes).
   - **Layer 2**: Statistical distribution (Z-score deviation, Interquartile Range fences).
   - **Layer 3**: Machine Learning (scikit-learn `IsolationForest`).
   - Translates raw mathematical outputs into human-friendly explanations.
4. **Budget Velocity & Projections**:
   - Calculates real-time spend velocity, remaining daily allowances, and projected month-end overruns.
5. **Smart CSV Import with Fuzzy Column Mapping**:
   - Auto-detects varied column names (`amount`, `price`, `merchant`, `description`, `date`, `category`, `payment_method`).
   - Automatically routes all imported transactions through categorization & anomaly detection.
6. **Agent Observability**:
   - Live audit trail of agent decisions, tool execution latency, arguments, and outcomes.
7. **Monthly Financial Intelligence Report**:
   - Automated breakdown with month-over-month comparisons and one-click PDF export.

---

## Quick Start (Local Development)

### 1. Start the Backend
```bash
# From project root
python3 -m pip install -r backend/requirements.txt
python3 -m backend.seed_data   # Seeds realistic demo scenarios
uvicorn backend.main:app --reload --port 8000
```
Backend API will be running at `http://localhost:8000`. API docs available at `http://localhost:8000/docs`.

### 2. Start the Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend will be running at `http://localhost:3000`.

Demo Credentials:
- **Email**: `demo@finagent.ai`
- **Password**: `finagent123`

---

## Cloud Deployment (Supabase + Vercel + Backend)

For a complete step-by-step walkthrough, see [`docs/DEPLOYMENT_GUIDE.md`](file:///Users/uakash/Desktop/SampleProject/docs/DEPLOYMENT_GUIDE.md).

1. **Database (Supabase)**:
   - Create a project at [Supabase](https://supabase.com).
   - Paste [`database/schema.sql`](file:///Users/uakash/Desktop/SampleProject/database/schema.sql) into Supabase SQL Editor and run it.
   - Copy your PostgreSQL connection URI.
2. **Backend (Render / Railway / Fly.io)**:
   - Deploy the Python FastAPI backend from `backend/`.
   - Set environment variables:
     - `DATABASE_URL`: `postgresql+psycopg2://postgres.[REF]:[PASS]@...:6543/postgres`
     - `OPENAI_API_KEY`: `sk-proj-...` (optional: built-in intelligent engine runs if omitted)
     - `SECRET_KEY`: `your-secure-jwt-key`
3. **Frontend (Vercel)**:
   - Import repository on [Vercel](https://vercel.com) with Root Directory `frontend`.
   - Set environment variable:
     - `NEXT_PUBLIC_API_URL`: `https://your-backend.onrender.com/api`
   - Deploy!

---

## Production Docker Deployment
```bash
docker-compose up --build
```
This deploys PostgreSQL 16 with the `pgvector` extension enabled, FastAPI backend, and Next.js frontend.

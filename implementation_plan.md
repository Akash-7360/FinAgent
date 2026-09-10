# FinAgent — Agentic Personal Expense Intelligence: Implementation Plan

FinAgent is an autonomous, production-quality Agentic AI platform designed for personalized expense intelligence. Rather than a static CRUD expense tracker, FinAgent executes autonomous multi-step reasoning: understanding unstructured input, categorizing with confidence metrics, retrieving personalized memory & similar transactions, evaluating budget velocity and projections, running multi-layer anomaly detection (Rule-based, Statistical Z-score/IQR, Isolation Forest ML), orchestrating dynamic LangGraph tool workflows, and triggering proactive notifications.

---

## User Review Required

> [!IMPORTANT]
> **Database & Vector Hybrid Strategy**:
> Since PostgreSQL/Docker is not running natively on the host machine, the backend database layer will use an adaptive SQLAlchemy engine:
> 1. In local dev mode, it defaults to SQLite with a NumPy/cosine similarity vector engine for transaction embeddings.
> 2. For Docker/Production deployment, `docker-compose.yml` and `database/schema.sql` provide PostgreSQL 16 with `pgvector` enabled (`vector(1536)`).
> This guarantees the application can run and be verified locally with zero external friction while fulfilling production Postgres + pgvector specs.

> [!TIP]
> **LLM Engine & Intelligent Fallback**:
> The LangGraph agent supports OpenAI API (`OPENAI_API_KEY`). To ensure 100% testability and reliability even without an active OpenAI API key or when network/quota limits occur, FinAgent includes an Intelligent Rule & Pattern-based Reasoning Fallback Engine that executes genuine LangGraph state transitions, tool selections, confidence calculations, anomaly evaluations, and natural language generation.

---

## Architecture Overview

```
finagent/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py             # JWT auth (register, login, me)
│   │   │   ├── expenses.py         # Expense CRUD + CSV auto-import with column mapper
│   │   │   ├── budgets.py          # Budget CRUD + velocity and alert thresholds
│   │   │   ├── analytics.py        # Monthly, category breakdowns, spending trends
│   │   │   ├── agent.py            # /api/agent/chat, /api/agent/analyze, /api/agent/events
│   │   │   ├── alerts.py           # Alerts list & resolve
│   │   │   └── reports.py          # Monthly automated report generator & PDF data
│   │   ├── agent/
│   │   │   ├── orchestrator.py     # LangGraph workflow, state graph, conditional routing
│   │   │   ├── tools.py            # 14 dynamic tools (add_expense, detect_anomaly, etc.)
│   │   │   ├── memory.py           # Personalized memory & vector similarity search
│   │   │   ├── categorizer.py      # Category + subcategory + confidence reasoning
│   │   │   └── proactive.py        # Autonomous periodic background monitoring
│   │   ├── ml/
│   │   │   ├── anomaly_detector.py # 3-Layer: Rules, Statistical (Z-score/IQR), Isolation Forest
│   │   │   └── models.py           # Model training & feature extraction pipeline
│   │   ├── core/
│   │   │   ├── config.py           # App settings & env
│   │   │   ├── security.py         # JWT tokens & passlib/bcrypt hashing
│   │   │   └── database.py         # SQLAlchemy session & DB models
│   │   ├── models/                 # SQLAlchemy ORM models (Users, Expenses, Budgets, Alerts, AgentEvents, etc.)
│   │   └── schemas/                # Pydantic validation schemas
│   ├── seed_data.py                # Comprehensive realistic seed data (demonstrates all 7 scenarios)
│   ├── requirements.txt
│   └── main.py                     # FastAPI entrypoint
├── frontend/                       # Next.js 14+ App Router with TypeScript & Tailwind CSS
│   ├── app/
│   │   ├── (auth)/login/page.tsx
│   │   ├── (dashboard)/
│   │   │   ├── page.tsx            # Modern Financial Dashboard
│   │   │   ├── transactions/       # Transactions with manual add + smart CSV importer
│   │   │   ├── budgets/            # Category Budgets & velocity tracker
│   │   │   ├── assistant/          # Conversational AI Assistant with tool step visualization
│   │   │   ├── insights/           # AI insights & spending patterns
│   │   │   ├── reports/            # Monthly report with printable/PDF export
│   │   │   ├── activity/           # Agent Observability & Event traces
│   │   │   └── settings/           # User preferences & thresholds
│   │   └── layout.tsx
│   ├── components/
│   │   ├── ui/                     # Glassmorphic, modern accessible components
│   │   ├── agent/                  # Tool execution trace, thinking states, confidence badges
│   │   ├── charts/                 # Recharts (Trend lines, Bar charts, Donut categories)
│   │   └── Navbar.tsx & Sidebar.tsx
│   ├── lib/                        # API client, formatting (₹ currency), auth context
│   └── package.json
├── database/
│   └── schema.sql                  # PostgreSQL + pgvector DDL schema
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml          # PostgreSQL 16 + pgvector + Backend + Frontend
└── README.md
```

---

## Detailed Components

### 1. Database & Schema
PostgreSQL/SQLite schemas for:
- `users`: id, email, hashed_password, full_name, currency (`INR` / `₹`), monthly_income, created_at.
- `user_preferences`: id, user_id, confidence_threshold (default 0.75), anomaly_sensitivity, alert_channels.
- `expenses`: id, user_id, amount, currency, category, subcategory, merchant, description, date, payment_method, confidence_score, categorization_reason, is_anomaly, anomaly_score, anomaly_reason, embedding (vector), is_recurring.
- `budgets`: id, user_id, category, monthly_limit, alert_threshold (e.g. 80%), period.
- `alerts`: id, user_id, title, message, alert_type (`anomaly`, `budget_warning`, `budget_exceeded`, `recurring_change`), severity (`low`, `medium`, `high`), expense_id, is_resolved, created_at.
- `agent_events`: id, user_id, timestamp, agent_state, tool_called, tool_arguments, tool_result_summary, decision, execution_time_ms, status.
- `recurring_expenses`: id, user_id, merchant, expected_amount, frequency, last_billed, next_expected.
- `monthly_reports`: id, user_id, month, year, total_spent, category_breakdown, top_expenses, anomaly_count, budget_adherence, ai_summary, recommendations.

### 2. Multi-Layer Anomaly Detection (`ml/anomaly_detector.py`)
- **Layer 1 (Rule-based)**:
  - Spike detection: `amount > 2.5 * user_category_average`.
  - First-time merchant with high-ticket value.
  - Frequency bursts within a short timeframe.
- **Layer 2 (Statistical)**:
  - Z-score computation on category and overall distribution: $Z = \frac{x - \mu}{\sigma}$ ($|Z| > 2.5$).
  - IQR bounds: $Q_3 + 1.5 \times \text{IQR}$.
  - Rolling 30-day velocity deviations.
- **Layer 3 (Machine Learning - Isolation Forest)**:
  - Trained on user transaction feature vectors: `[amount, category_encoded, day_of_week, hour_of_day, merchant_freq, deviation_from_normal]`.
  - Computes anomaly score in range $[0, 1]$.
- **Composite Scorer & Agent Interpretation**:
  - Blends the 3 layers into a single normalized risk score.
  - Translates mathematical outputs into human-friendly explanations (e.g. "₹4,500 at restaurant is 4.2x above your 90-day typical restaurant spend of ₹850").

### 3. Core LangGraph Orchestrator (`backend/app/agent/`)
- **Graph State**:
  - `messages`: Chat message history.
  - `current_input`: Raw text or transaction data.
  - `intent`: Classified intent (`add_expense`, `analyze_spending`, `budget_query`, `general_inquiry`).
  - `extracted_entities`: Amount, merchant, date, category hints.
  - `categorization`: Category, subcategory, confidence score, reasoning.
  - `needs_clarification`: Boolean flag if confidence < user threshold.
  - `tool_calls_pending`: Queue of tools to execute.
  - `tool_results`: Dictionary of tool outputs.
  - `anomaly_result`: Anomaly score, is_anomaly, explanation.
  - `budget_status`: Current budget vs remaining and velocity.
  - `final_response`: Formatted response.
- **Dynamic Conditional Transitions**:
  - `perceive_node` -> `classify_intent_node`.
  - If low confidence categorization -> `ask_clarification_node`.
  - If high confidence -> `plan_tools_node` -> `execute_tools_node` (dynamic routing) -> `reason_observe_node` -> `generate_insight_node` -> `audit_event_node`.
- **14 Tools**:
  - `add_expense`: Validates and commits expense record.
  - `get_expense_history`: Filtered historical transactions.
  - `get_category_spending`: Aggregates for specific category.
  - `get_monthly_spending`: Month-by-month sums.
  - `get_merchant_history`: Historical transactions for a merchant.
  - `search_similar_transactions`: Vector & text similarity lookup.
  - `check_budget`: Checks limits, spent so far, and remaining balance.
  - `create_budget`: Sets category monthly limit.
  - `update_budget`: Modifies existing budget.
  - `detect_anomaly`: Runs the 3-layer anomaly engine.
  - `calculate_spending_trend`: Calculates month-over-month velocity.
  - `generate_monthly_report`: Compiles comprehensive monthly analysis.
  - `create_alert`: Persists proactive notification.
  - `get_user_preferences`: Loads user thresholds and settings.

### 4. Natural Language Conversational Interface & Observability
- Seamless natural language parsing for queries like:
  - *"I spent ₹4,500 at a restaurant."*
  - *"Paid ₹2,500 to Rahul"* (triggers low-confidence clarification request)
  - *"Am I spending too much on food?"*
  - *"Create a ₹5,000 entertainment budget."*
  - *"Show my biggest expenses and find unusual spending."*
- Chat UI shows tool activity chips:
  - `[✓] Analyzed input: ₹4,500 at Restaurant`
  - `[✓] Category: Food (Confidence: 96%)`
  - `[✓] Anomaly Check: Score 0.88 (Unusually high)`
  - `[✓] Budget Check: Food budget 86% utilized`
  - `[✓] Saved Expense & Created Alert`
- Dedicated **Agent Activity** tab displays full timeline audits of agent state, selected tools, execution time, and decisions.

### 5. Frontend (Next.js, TypeScript, Tailwind CSS, Recharts)
- Premium dark/light theme with glassmorphic cards, vibrant metrics, and smooth Framer Motion transitions.
- **Pages**:
  - **Dashboard**: Monthly metrics, budget gauges, spending trend charts, category donut, top merchants, anomaly alerts banner, AI Insights card.
  - **Transactions**: Full data table with filters, search, manual entry modal, and Smart CSV Import with drag-and-drop & fuzzy column mapping (`amount`, `price`, `merchant`, `description`, `date`, `category`, etc.).
  - **Budgets**: Category budget cards, visual progress bars, velocity projection ("projected to exceed by 15%"), create/edit budget modal.
  - **AI Assistant**: Rich chat interface with dynamic quick-prompts, streaming-like feel, and expandable step-by-step tool execution traces.
  - **Insights & Anomalies**: Deep dive into detected anomalies with rule, stats, and ML breakdown; recurring expense tracker.
  - **Reports**: Automated monthly report view with MoM charts, top categories, AI recommendations, and one-click PDF/print export.
  - **Agent Activity**: Full audit trail of agent executions, reasoning steps, tool calls, and execution latencies.
  - **Settings**: Profile, monthly income, currency selector, and agent sensitivity thresholds.

### 6. Realistic Seed Data Scenarios
The seed dataset will populate:
1. Normal everyday transactions (groceries, metro, coffee, lunch).
2. High-value anomaly (e.g. ₹4,500 luxury restaurant or ₹35,000 electronics spike).
3. Low-confidence transaction (e.g. "Paid ₹2,500 to Rahul" marked for clarification).
4. Budget warning (Transport nearing 85%).
5. Budget exceeded (Shopping at 110%).
6. Spending trend (Food up 27% MoM).
7. Recurring subscriptions (Netflix, Spotify, AWS, Gym).

---

## Verification Plan

### Automated Verification
1. **Backend Tests**:
   - `python3 -m pytest backend/tests` or standalone test scripts:
     - Authentication endpoints (register, login, JWT token verification).
     - Anomaly detection 3-layer engine tests (rules, Z-score, Isolation Forest).
     - Agent orchestrator test (tool routing, multi-step execution, clarification on ambiguous transactions).
     - Budget tracking and velocity projection calculation.
     - CSV import with varied header formats.
2. **Frontend Build & Lint**:
   - `npm run build` in `frontend/` to verify zero TypeScript or syntax errors.

### Manual Verification via Browser Subagent
1. Run backend FastAPI server on `http://127.0.0.1:8000`.
2. Run frontend Next.js dev server on `http://127.0.0.1:3000`.
3. Use browser subagent to:
   - Login with demo user credentials.
   - Verify dashboard metrics, Recharts, and AI Insights.
   - Enter the exact test scenario: *"₹4,500 — Restaurant — Today"* and verify the agent workflow steps (Categorization -> Anomaly score -> Budget check -> Alert generated).
   - Enter ambiguous scenario: *"Paid ₹2,500 to Rahul"* and verify the clarification prompt.
   - Ask: *"Am I spending too much on food?"* and verify dynamic tool calling and recommendations.
   - Test CSV transaction import with sample CSV file.
   - Test Monthly Report view and print/PDF export preview.
   - View Agent Activity page to confirm audit traces.

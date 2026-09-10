# FinAgent Architecture Overview

FinAgent is an advanced Agentic AI personal expense intelligence application built on a modern full-stack decoupled architecture.

```
+-------------------------------------------------------------+
|                  Next.js Modern Frontend                    |
|  (TypeScript, Tailwind CSS, Recharts, Lucide, Framer Motion)|
+-------------------------------------------------------------+
                              |
                     REST APIs / JWT Auth
                              |
+-------------------------------------------------------------+
|                     FastAPI Backend                         |
|  - Auth & Security (Bcrypt, PyJWT)                          |
|  - Expenses Engine & Fuzzy CSV Importer                     |
|  - Budget & Velocity Projection                             |
|  - Analytics & Report Generator                             |
|  - Background Proactive Scheduler (APScheduler)             |
+-------------------------------------------------------------+
          |                                  |
+----------------------+           +--------------------------+
| LangGraph Orchestrator|          | 3-Layer Anomaly Engine   |
| - State Graph        |           | - Layer 1: Rules/Heuristics|
| - 14 Dynamic Tools   |           | - Layer 2: Z-Score & IQR |
| - Clarification Loop |           | - Layer 3: Isolation     |
| - Observability Traces|          |            Forest (ML)   |
+----------------------+           +--------------------------+
          |                                  |
+-------------------------------------------------------------+
|                    Database Layer                           |
| - PostgreSQL 16 + pgvector (Docker/Production)              |
| - SQLite + Semantic Vector Engine (Seamless Local Dev)      |
+-------------------------------------------------------------+
```

## Agentic Loop Design
1. **Perceive**: Extract numeric amounts, merchants, categories, and query intents.
2. **Confidence Verification**: Evaluate categorization confidence score against configurable threshold (default 0.75). Ambiguous peer transfers (e.g. "Paid ₹2,500 to Rahul") trigger an interactive clarification state rather than committing guessed data.
3. **Plan**: Dynamically select required tools based on context.
4. **Execute**: Run tools through LangGraph nodes.
5. **Observe & Reason**: Inspect intermediate results; if anomaly signals or budget warnings arise, dynamically generate alerts.
6. **Synthesize & Audit**: Deliver natural language explanations and log execution traces into `agent_events`.

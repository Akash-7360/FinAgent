# FinAgent API Reference

Base URL: `http://localhost:8000/api`

## Authentication
- `POST /api/auth/register`: Register user with email, password, full name, income.
- `POST /api/auth/login`: Authenticate and receive JWT token.
- `GET /api/auth/me`: Get current user profile and preferences.
- `PUT /api/auth/preferences`: Update confidence threshold, anomaly sensitivity, dark mode.

## Expenses
- `GET /api/expenses`: List expenses with query filters (`category`, `merchant`, `start_date`, `end_date`, `is_anomaly`).
- `POST /api/expenses`: Log expense, automatically triggering anomaly detection and budget check.
- `GET /api/expenses/{id}`: Retrieve single expense.
- `DELETE /api/expenses/{id}`: Remove an expense.
- `POST /api/expenses/import`: Multipart form upload with CSV file. Smart fuzzy column mapping detects amount, merchant, date, and category.

## Budgets
- `GET /api/budgets`: List category budgets with spent amounts, remaining funds, percentage, and velocity status (`safe`, `warning`, `exceeded`).
- `POST /api/budgets`: Create or update category budget.
- `PUT /api/budgets/{id}`: Modify budget limits or thresholds.
- `DELETE /api/budgets/{id}`: Delete a budget.

## Agent Orchestrator & Observability
- `POST /api/agent/chat`: Full LangGraph conversational orchestrator endpoint. Accepts user prompt, returns agent response, tool execution traces, insights, and created alert/expense.
- `POST /api/agent/analyze`: Parse natural language text for extracted entities and categorization confidence without committing.
- `GET /api/agent/events`: Audit trail of all agent states, tool arguments, decisions, and execution latency.
- `POST /api/agent/proactive/trigger`: Manually trigger background anomaly and duplicate charge scan.

## Analytics & Reports
- `GET /api/analytics/summary`: Key metrics, month-over-month percentage change, top merchant, and AI insights.
- `GET /api/analytics/monthly`: Monthly spending totals and transaction counts.
- `GET /api/analytics/categories`: Category breakdown with percentages.
- `GET /api/analytics/trends`: Daily spending velocity over time.
- `POST /api/reports/monthly`: Generate automated monthly intelligence report.
- `GET /api/reports/monthly`: List historical generated monthly reports.

## Alerts
- `GET /api/alerts`: List unresolved or all notifications.
- `POST /api/alerts/{id}/resolve`: Mark an alert as resolved.

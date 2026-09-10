-- ==========================================================
-- FinAgent PostgreSQL + pgvector Database Schema
-- Production DDL with vector embeddings and audit logging
-- ==========================================================

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    currency VARCHAR(10) DEFAULT '₹',
    monthly_income NUMERIC(12, 2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. User Preferences Table
CREATE TABLE IF NOT EXISTS user_preferences (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    confidence_threshold NUMERIC(3, 2) DEFAULT 0.75,
    anomaly_sensitivity NUMERIC(3, 2) DEFAULT 0.70,
    budget_alert_threshold NUMERIC(3, 2) DEFAULT 0.80,
    enable_proactive_alerts BOOLEAN DEFAULT TRUE,
    dark_mode BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Expenses Table
CREATE TABLE IF NOT EXISTS expenses (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount NUMERIC(12, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT '₹',
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(50),
    merchant VARCHAR(100) NOT NULL,
    description TEXT,
    date DATE NOT NULL,
    payment_method VARCHAR(50) DEFAULT 'Card',
    confidence_score NUMERIC(4, 3) DEFAULT 1.0,
    categorization_reason TEXT,
    is_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_score NUMERIC(4, 3) DEFAULT 0.0,
    anomaly_reason TEXT,
    is_recurring BOOLEAN DEFAULT FALSE,
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_expenses_user_date ON expenses(user_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(user_id, category);
CREATE INDEX IF NOT EXISTS idx_expenses_merchant ON expenses(user_id, merchant);

-- 4. Budgets Table
CREATE TABLE IF NOT EXISTS budgets (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,
    monthly_limit NUMERIC(12, 2) NOT NULL,
    alert_threshold NUMERIC(3, 2) DEFAULT 0.80,
    period VARCHAR(20) DEFAULT 'monthly',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_category UNIQUE (user_id, category)
);

-- 5. Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    alert_type VARCHAR(50) NOT NULL, -- anomaly, budget_warning, budget_exceeded, recurring_change
    severity VARCHAR(20) DEFAULT 'medium', -- low, medium, high, critical
    expense_id VARCHAR(36) REFERENCES expenses(id) ON DELETE SET NULL,
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alerts_user_resolved ON alerts(user_id, is_resolved);

-- 6. Agent Events Table (Observability & Audit Trail)
CREATE TABLE IF NOT EXISTS agent_events (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    agent_state VARCHAR(50) NOT NULL,
    tool_called VARCHAR(100),
    tool_arguments JSONB,
    tool_result_summary TEXT,
    decision TEXT NOT NULL,
    execution_time_ms INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'success'
);

CREATE INDEX IF NOT EXISTS idx_agent_events_user ON agent_events(user_id, timestamp DESC);

-- 7. Recurring Expenses Table
CREATE TABLE IF NOT EXISTS recurring_expenses (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    merchant VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    expected_amount NUMERIC(12, 2) NOT NULL,
    frequency VARCHAR(20) DEFAULT 'monthly',
    last_billed DATE,
    next_expected DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. Monthly Reports Table
CREATE TABLE IF NOT EXISTS monthly_reports (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    total_spent NUMERIC(12, 2) NOT NULL,
    category_breakdown JSONB NOT NULL,
    top_expenses JSONB NOT NULL,
    anomaly_count INTEGER DEFAULT 0,
    budget_adherence JSONB,
    ai_summary TEXT,
    recommendations JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_month_year UNIQUE (user_id, month, year)
);

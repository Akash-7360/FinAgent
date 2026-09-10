import uuid
from datetime import datetime, date, timezone
from sqlalchemy import (
    Column, String, Numeric, Boolean, Date, DateTime, Text, Integer, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    currency = Column(String(10), default="₹")
    monthly_income = Column(Numeric(12, 2), default=0.00)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    agent_events = relationship("AgentEvent", back_populates="user", cascade="all, delete-orphan")
    recurring_expenses = relationship("RecurringExpense", back_populates="user", cascade="all, delete-orphan")
    monthly_reports = relationship("MonthlyReport", back_populates="user", cascade="all, delete-orphan")

class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    confidence_threshold = Column(Numeric(3, 2), default=0.75)
    anomaly_sensitivity = Column(Numeric(3, 2), default=0.70)
    budget_alert_threshold = Column(Numeric(3, 2), default=0.80)
    enable_proactive_alerts = Column(Boolean, default=True)
    dark_mode = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="preferences")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="₹")
    category = Column(String(50), nullable=False, index=True)
    subcategory = Column(String(50), nullable=True)
    merchant = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    date = Column(Date, nullable=False, index=True)
    payment_method = Column(String(50), default="Card")
    confidence_score = Column(Numeric(4, 3), default=1.0)
    categorization_reason = Column(Text, nullable=True)
    is_anomaly = Column(Boolean, default=False)
    anomaly_score = Column(Numeric(4, 3), default=0.0)
    anomaly_reason = Column(Text, nullable=True)
    is_recurring = Column(Boolean, default=False)
    # Stored as JSON serialized float array for portable SQLite/Postgres vector compatibility
    embedding = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("User", back_populates="expenses")
    alerts = relationship("Alert", back_populates="expense")

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(50), nullable=False)
    monthly_limit = Column(Numeric(12, 2), nullable=False)
    alert_threshold = Column(Numeric(3, 2), default=0.80)
    period = Column(String(20), default="monthly")
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="budgets")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    alert_type = Column(String(50), nullable=False) # anomaly, budget_warning, budget_exceeded, recurring_change
    severity = Column(String(20), default="medium") # low, medium, high, critical
    expense_id = Column(String(36), ForeignKey("expenses.id", ondelete="SET NULL"), nullable=True)
    is_resolved = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("User", back_populates="alerts")
    expense = relationship("Expense", back_populates="alerts")

class AgentEvent(Base):
    __tablename__ = "agent_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)
    agent_state = Column(String(50), nullable=False)
    tool_called = Column(String(100), nullable=True)
    tool_arguments = Column(JSON, nullable=True)
    tool_result_summary = Column(Text, nullable=True)
    decision = Column(Text, nullable=False)
    execution_time_ms = Column(Integer, default=0)
    status = Column(String(20), default="success")

    user = relationship("User", back_populates="agent_events")

class RecurringExpense(Base):
    __tablename__ = "recurring_expenses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    merchant = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    expected_amount = Column(Numeric(12, 2), nullable=False)
    frequency = Column(String(20), default="monthly")
    last_billed = Column(Date, nullable=True)
    next_expected = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("User", back_populates="recurring_expenses")

class MonthlyReport(Base):
    __tablename__ = "monthly_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    total_spent = Column(Numeric(12, 2), nullable=False)
    category_breakdown = Column(JSON, nullable=False)
    top_expenses = Column(JSON, nullable=False)
    anomaly_count = Column(Integer, default=0)
    budget_adherence = Column(JSON, nullable=True)
    ai_summary = Column(Text, nullable=True)
    recommendations = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("User", back_populates="monthly_reports")

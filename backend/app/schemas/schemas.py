from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime

# --- Auth & User Schemas ---
class UserCreate(BaseModel):
    email: str
    password: str = Field(..., min_length=6)
    full_name: str
    currency: Optional[str] = "₹"
    monthly_income: Optional[float] = 0.0

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class UserPreferenceUpdate(BaseModel):
    confidence_threshold: Optional[float] = None
    anomaly_sensitivity: Optional[float] = None
    budget_alert_threshold: Optional[float] = None
    enable_proactive_alerts: Optional[bool] = None
    dark_mode: Optional[bool] = None

class UserPreferenceResponse(BaseModel):
    confidence_threshold: float
    anomaly_sensitivity: float
    budget_alert_threshold: float
    enable_proactive_alerts: bool
    dark_mode: bool

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    currency: str
    monthly_income: float
    preferences: Optional[UserPreferenceResponse] = None

    class Config:
        from_attributes = True

# --- Expense Schemas ---
class ExpenseCreate(BaseModel):
    amount: float = Field(..., gt=0)
    category: Optional[str] = None
    subcategory: Optional[str] = None
    merchant: str
    description: Optional[str] = None
    date: Optional[date] = None
    payment_method: Optional[str] = "Card"
    currency: Optional[str] = "₹"
    confidence_score: Optional[float] = 1.0
    categorization_reason: Optional[str] = None
    is_recurring: Optional[bool] = False

class ExpenseUpdate(BaseModel):
    amount: Optional[float] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    merchant: Optional[str] = None
    description: Optional[str] = None
    date: Optional[date] = None
    payment_method: Optional[str] = None

class ExpenseResponse(BaseModel):
    id: str
    user_id: str
    amount: float
    currency: str
    category: str
    subcategory: Optional[str] = None
    merchant: str
    description: Optional[str] = None
    date: date
    payment_method: str
    confidence_score: float
    categorization_reason: Optional[str] = None
    is_anomaly: bool
    anomaly_score: float
    anomaly_reason: Optional[str] = None
    is_recurring: bool
    created_at: datetime

    class Config:
        from_attributes = True

# --- Budget Schemas ---
class BudgetCreate(BaseModel):
    category: str
    monthly_limit: float = Field(..., gt=0)
    alert_threshold: Optional[float] = 0.80
    period: Optional[str] = "monthly"

class BudgetUpdate(BaseModel):
    monthly_limit: Optional[float] = Field(None, gt=0)
    alert_threshold: Optional[float] = None

class BudgetResponse(BaseModel):
    id: str
    user_id: str
    category: str
    monthly_limit: float
    alert_threshold: float
    period: str
    spent_so_far: Optional[float] = 0.0
    remaining_amount: Optional[float] = 0.0
    percentage_used: Optional[float] = 0.0
    is_exceeded: Optional[bool] = False
    projected_spend: Optional[float] = 0.0
    velocity_status: Optional[str] = "normal" # safe, warning, exceeded
    created_at: datetime

    class Config:
        from_attributes = True

# --- Alert Schemas ---
class AlertResponse(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    alert_type: str
    severity: str
    expense_id: Optional[str] = None
    is_resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True

# --- Agent Schemas ---
class AgentChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class ToolExecutionTrace(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result: Any
    timestamp: str

class AgentChatResponse(BaseModel):
    response: str
    requires_clarification: bool = False
    clarification_prompt: Optional[str] = None
    suggested_categories: Optional[List[str]] = None
    pending_transaction: Optional[Dict[str, Any]] = None
    tools_executed: List[ToolExecutionTrace] = []
    insights: Optional[List[str]] = []
    created_expense: Optional[Dict[str, Any]] = None
    created_alert: Optional[Dict[str, Any]] = None

class AgentAnalyzeRequest(BaseModel):
    text: str
    date: Optional[date] = None

class AgentEventResponse(BaseModel):
    id: str
    user_id: str
    timestamp: datetime
    agent_state: str
    tool_called: Optional[str] = None
    tool_arguments: Optional[Dict[str, Any]] = None
    tool_result_summary: Optional[str] = None
    decision: str
    execution_time_ms: int
    status: str

    class Config:
        from_attributes = True

# --- Analytics Schemas ---
class CategorySpendingItem(BaseModel):
    category: str
    total_amount: float
    count: int
    percentage: float

class MonthlySpendingItem(BaseModel):
    month_name: str
    month: int
    year: int
    total_amount: float
    transaction_count: int

class SpendingTrendItem(BaseModel):
    date: str
    amount: float
    category: str

# --- Report Schemas ---
class MonthlyReportResponse(BaseModel):
    id: str
    month: int
    year: int
    total_spent: float
    category_breakdown: Dict[str, float]
    top_expenses: List[Dict[str, Any]]
    anomaly_count: int
    budget_adherence: Optional[Dict[str, Any]] = None
    ai_summary: Optional[str] = None
    recommendations: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True

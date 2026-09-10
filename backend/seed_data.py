import uuid
from datetime import date, timedelta, datetime, timezone
import random
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal, engine, Base
from backend.app.core.security import hash_password
from backend.app.models.entities import (
    User, UserPreference, Expense, Budget, Alert, AgentEvent, RecurringExpense, MonthlyReport
)
from backend.app.agent.memory import compute_text_embedding

def seed_default_data(db: Session):
    # Check if demo user already exists
    demo_user = db.query(User).filter(User.email == "demo@finagent.ai").first()
    if demo_user:
        return demo_user

    print("🌱 Seeding realistic FinAgent demo scenarios...")

    # 1. Create Demo User
    demo_user = User(
        id=str(uuid.uuid4()),
        email="demo@finagent.ai",
        hashed_password=hash_password("finagent123"),
        full_name="Akash U",
        currency="₹",
        monthly_income=125000.00
    )
    db.add(demo_user)
    db.commit()
    db.refresh(demo_user)

    # 2. User Preferences
    pref = UserPreference(
        user_id=demo_user.id,
        confidence_threshold=0.75,
        anomaly_sensitivity=0.70,
        budget_alert_threshold=0.80,
        enable_proactive_alerts=True,
        dark_mode=True
    )
    db.add(pref)

    today = date.today()

    # 3. Budgets demonstrating:
    # - Budget warning: Transport (limit 4000, spent 3450 = 86%)
    # - Budget exceeded: Shopping (limit 15000, spent 16800 = 112%)
    # - Food budget (limit 12000, currently 10200 = 85% velocity warning)
    # - Entertainment budget (limit 5000, spent 2200 = safe)
    # - Groceries budget (limit 10000, spent 6800 = safe)
    budgets = [
        Budget(user_id=demo_user.id, category="Food", monthly_limit=12000.0, alert_threshold=0.80),
        Budget(user_id=demo_user.id, category="Transport", monthly_limit=4000.0, alert_threshold=0.80),
        Budget(user_id=demo_user.id, category="Shopping", monthly_limit=15000.0, alert_threshold=0.80),
        Budget(user_id=demo_user.id, category="Entertainment", monthly_limit=5000.0, alert_threshold=0.80),
        Budget(user_id=demo_user.id, category="Groceries", monthly_limit=10000.0, alert_threshold=0.80),
        Budget(user_id=demo_user.id, category="Subscriptions", monthly_limit=4500.0, alert_threshold=0.80),
    ]
    db.add_all(budgets)

    # 4. Recurring Subscriptions
    subs = [
        RecurringExpense(user_id=demo_user.id, merchant="Netflix", category="Subscriptions", expected_amount=649.00, frequency="monthly", last_billed=today - timedelta(days=12)),
        RecurringExpense(user_id=demo_user.id, merchant="Spotify", category="Subscriptions", expected_amount=119.00, frequency="monthly", last_billed=today - timedelta(days=18)),
        RecurringExpense(user_id=demo_user.id, merchant="AWS Cloud", category="Subscriptions", expected_amount=2840.00, frequency="monthly", last_billed=today - timedelta(days=5)),
        RecurringExpense(user_id=demo_user.id, merchant="Cult.fit Gym", category="Healthcare", expected_amount=2500.00, frequency="monthly", last_billed=today - timedelta(days=22)),
    ]
    db.add_all(subs)

    # 5. Populate Historical Expenses for:
    # - Last month (lower food spending to demonstrate Food up 27% MoM trend)
    # - Typical restaurant spending: ₹400 - ₹900 range (averaging ~₹650)
    # - Current month normal transactions

    expenses = []

    # Historical Previous Month Expenses (Food totaled ~₹7,500)
    for d_offset in range(35, 60, 2):
        exp_date = today - timedelta(days=d_offset)
        # Normal restaurant lunch/dinner in past month
        amt = random.choice([420, 550, 680, 750, 890])
        expenses.append(Expense(
            user_id=demo_user.id,
            amount=amt,
            merchant=random.choice(["Udipi Bhavan", "Chai Point", "Swiggy", "Subway", "Cafe Coffee Day"]),
            category="Food",
            subcategory="Dining Out",
            description="Regular lunch / dinner meal",
            date=exp_date,
            confidence_score=0.98,
            categorization_reason="Identified dining merchant",
            is_anomaly=False,
            anomaly_score=0.08,
            embedding=compute_text_embedding(f"Food dining restaurant {amt}")
        ))

    # Current Month Normal Transactions
    # A) Normal Groceries & Everyday spend
    for d_offset in range(1, 25, 3):
        exp_date = today - timedelta(days=d_offset)
        expenses.append(Expense(
            user_id=demo_user.id,
            amount=random.choice([850, 1240, 1650, 990]),
            merchant=random.choice(["Blinkit", "Nature's Basket", "Zepto", "BigBasket"]),
            category="Groceries",
            subcategory="Supermarket",
            description="Weekly groceries & household essentials",
            date=exp_date,
            confidence_score=0.97,
            categorization_reason="Recognized grocery vendor",
            is_anomaly=False,
            anomaly_score=0.05,
            embedding=compute_text_embedding("Groceries Blinkit Zepto")
        ))

    # B) Transport approaching 86% warning: Uber rides accumulating
    for d_offset in [2, 4, 7, 9, 12, 14, 16, 19]:
        exp_date = today - timedelta(days=d_offset)
        amt = random.choice([380, 420, 450, 490])
        expenses.append(Expense(
            user_id=demo_user.id,
            amount=amt,
            merchant="Uber India",
            category="Transport",
            subcategory="Rideshare & Cabs",
            description="Commute rideshare",
            date=exp_date,
            confidence_score=0.99,
            categorization_reason="Matched transit keyword",
            is_anomaly=False,
            anomaly_score=0.06,
            embedding=compute_text_embedding("Transport Uber cab")
        ))

    # C) Shopping exceeding budget (₹16,800 spent vs ₹15,000 limit)
    expenses.append(Expense(
        user_id=demo_user.id,
        amount=11999.00,
        merchant="Amazon",
        category="Shopping",
        subcategory="Electronics",
        description="Noise Cancelling Headphones",
        date=today - timedelta(days=10),
        confidence_score=0.98,
        categorization_reason="Premier e-commerce marketplace",
        is_anomaly=False,
        anomaly_score=0.28,
        embedding=compute_text_embedding("Shopping Amazon electronics")
    ))
    expenses.append(Expense(
        user_id=demo_user.id,
        amount=4800.00,
        merchant="Zara",
        category="Shopping",
        subcategory="Apparel",
        description="Winter jacket",
        date=today - timedelta(days=6),
        confidence_score=0.96,
        categorization_reason="Clothing retail merchant",
        is_anomaly=False,
        anomaly_score=0.22,
        embedding=compute_text_embedding("Shopping Zara apparel")
    ))

    # D) High-value anomaly: ₹4,500 Restaurant expense (vs normal ₹600-900)
    anomaly_expense = Expense(
        user_id=demo_user.id,
        amount=4500.00,
        merchant="Bastian Fine Dining",
        category="Food",
        subcategory="Restaurant",
        description="Luxury celebration dinner",
        date=today - timedelta(days=1),
        confidence_score=0.96,
        categorization_reason="Identified restaurant dining activity",
        is_anomaly=True,
        anomaly_score=0.89,
        anomaly_reason="Exceeds typical Food spending (₹650 avg) by 6.9x • Statistical deviation: Z-score is 3.8σ above distribution • Multi-dimensional pattern anomaly identified by Isolation Forest",
        embedding=compute_text_embedding("Food Bastian fine dining restaurant celebration")
    )
    expenses.append(anomaly_expense)

    # E) Low-confidence transaction: "Paid ₹2,500 to Rahul"
    clarification_expense = Expense(
        user_id=demo_user.id,
        amount=2500.00,
        merchant="Rahul",
        category="Transfers",
        subcategory="Peer-to-Peer",
        description="Paid ₹2,500 to Rahul",
        date=today - timedelta(days=3),
        confidence_score=0.45,
        categorization_reason="Payment to individual 'Rahul' without specified purpose.",
        is_anomaly=False,
        anomaly_score=0.20,
        embedding=compute_text_embedding("Transfers peer Rahul payment")
    )
    expenses.append(clarification_expense)

    db.add_all(expenses)
    db.commit()

    # 6. Seed Alerts
    alerts = [
        Alert(
            user_id=demo_user.id,
            title="⚠️ Unusual spending detected: ₹4,500 at Bastian Fine Dining",
            message="You spent ₹4,500 at Bastian Fine Dining. This is significantly higher than your typical restaurant spending of ₹600–₹900 (6.9x normal average).",
            alert_type="anomaly",
            severity="high",
            expense_id=anomaly_expense.id,
            is_resolved=False
        ),
        Alert(
            user_id=demo_user.id,
            title="🚨 Budget Exceeded: Shopping",
            message="You have spent ₹16,799 exceeding your monthly Shopping limit of ₹15,000 (112% utilized).",
            alert_type="budget_exceeded",
            severity="high",
            is_resolved=False
        ),
        Alert(
            user_id=demo_user.id,
            title="⚠️ Budget Approaching Limit: Transport",
            message="Transport spending is at 86% (₹3,450 / ₹4,000 limit). You are projected to exceed this budget at current velocity.",
            alert_type="budget_warning",
            severity="medium",
            is_resolved=False
        ),
        Alert(
            user_id=demo_user.id,
            title="❓ Clarification Required: Payment to Rahul",
            message="Payment of ₹2,500 to Rahul was logged with low confidence. Was this a personal transfer, dinner split, or loan repayment?",
            alert_type="anomaly",
            severity="low",
            expense_id=clarification_expense.id,
            is_resolved=False
        )
    ]
    db.add_all(alerts)

    # 7. Seed Agent Observability Events
    agent_events = [
        AgentEvent(
            user_id=demo_user.id,
            agent_state="Perceive",
            tool_called=None,
            tool_arguments={"input": "₹4,500 — Restaurant — Today"},
            tool_result_summary="Detected amount: ₹4,500, merchant: Bastian Restaurant, category: Food",
            decision="Identified high-priority financial transaction input.",
            execution_time_ms=15,
            status="success"
        ),
        AgentEvent(
            user_id=demo_user.id,
            agent_state="Tool_Execution",
            tool_called="detect_anomaly",
            tool_arguments={"amount": 4500.0, "category": "Food", "merchant": "Bastian"},
            tool_result_summary="Anomaly score: 0.89. Exceeds typical restaurant spending by 6.9x.",
            decision="Anomaly threshold exceeded (0.89 >= 0.70). High-risk signal confirmed.",
            execution_time_ms=85,
            status="success"
        ),
        AgentEvent(
            user_id=demo_user.id,
            agent_state="Tool_Execution",
            tool_called="check_budget",
            tool_arguments={"category": "Food"},
            tool_result_summary="Food budget: 85% utilized (₹10,200 / ₹12,000).",
            decision="Velocity projection indicates imminent overrun if trajectory continues.",
            execution_time_ms=32,
            status="success"
        ),
        AgentEvent(
            user_id=demo_user.id,
            agent_state="Autonomous_Alert_Triggered",
            tool_called="create_alert",
            tool_arguments={"title": "⚠️ Unusual spending detected: ₹4,500 at Bastian Fine Dining"},
            tool_result_summary="Alert ID generated and stored in audit ledger.",
            decision="Dispatched proactive alert to user dashboard.",
            execution_time_ms=22,
            status="success"
        ),
        AgentEvent(
            user_id=demo_user.id,
            agent_state="Awaiting_Clarification",
            tool_called="categorize_transaction",
            tool_arguments={"text": "Paid ₹2,500 to Rahul"},
            tool_result_summary="Confidence: 0.45 (< 0.75 threshold). Peer recipient identified.",
            decision="Halted automated categorization to prevent ledger inaccuracy.",
            execution_time_ms=18,
            status="success"
        )
    ]
    db.add_all(agent_events)

    db.commit()
    print("✅ Seed data successfully committed.")
    return demo_user

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_default_data(db)
    finally:
        db.close()

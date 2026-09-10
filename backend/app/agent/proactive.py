import logging
from datetime import date, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from backend.app.models.entities import User, Expense, Budget, Alert, UserPreference
from backend.app.agent.tools import AgentTools

logger = logging.getLogger("proactive_monitor")

class ProactiveMonitor:
    """Autonomous scheduler engine that scans for budget overruns, duplicates, and anomalies."""

    def __init__(self, db: Session):
        self.db = db

    def scan_user(self, user_id: str) -> List[Dict[str, Any]]:
        generated_alerts = []
        tools = AgentTools(self.db, user_id)
        prefs = tools.get_user_preferences()

        if not prefs.get("enable_proactive_alerts", True):
            return []

        # 1. Scan budgets for approaching limit (e.g. >= 80%) or exceeded
        budgets = self.db.query(Budget).filter(Budget.user_id == user_id).all()
        for b in budgets:
            b_status = tools.check_budget(b.category)
            if b_status.get("is_exceeded"):
                # Check if alert already exists today
                existing = self.db.query(Alert).filter(
                    Alert.user_id == user_id,
                    Alert.title.ilike(f"%exceeded {b.category}%"),
                    Alert.is_resolved == False
                ).first()
                if not existing:
                    alert = tools.create_alert(
                        title=f"🚨 Budget Exceeded: {b.category}",
                        message=f"You have spent ₹{b_status['spent_so_far']:,.2f} exceeding your monthly {b.category} limit of ₹{b_status['monthly_limit']:,.2f}.",
                        alert_type="budget_exceeded",
                        severity="high"
                    )
                    generated_alerts.append(alert)

            elif b_status.get("status") == "warning":
                existing = self.db.query(Alert).filter(
                    Alert.user_id == user_id,
                    Alert.title.ilike(f"%approaching limit: {b.category}%"),
                    Alert.is_resolved == False
                ).first()
                if not existing:
                    alert = tools.create_alert(
                        title=f"⚠️ Budget Approaching Limit: {b.category}",
                        message=f"{b.category} spending is at {b_status['percentage_used']}% (₹{b_status['spent_so_far']:,.2f}/₹{b_status['monthly_limit']:,.2f}). {b_status['recommendation']}",
                        alert_type="budget_warning",
                        severity="medium"
                    )
                    generated_alerts.append(alert)

        # 2. Check for duplicate-looking transactions in the last 7 days
        recent = self.db.query(Expense).filter(
            Expense.user_id == user_id,
            Expense.date >= date.today() - timedelta(days=7)
        ).all()

        seen_pairs: Dict[str, List[Expense]] = {}
        for exp in recent:
            key = f"{exp.merchant.lower()}_{float(exp.amount)}"
            seen_pairs.setdefault(key, []).append(exp)

        for key, exp_list in seen_pairs.items():
            if len(exp_list) > 1:
                # Potential duplicate charge!
                merchant = exp_list[0].merchant
                amt = float(exp_list[0].amount)
                existing = self.db.query(Alert).filter(
                    Alert.user_id == user_id,
                    Alert.title.ilike(f"%Possible duplicate charge at {merchant}%"),
                    Alert.is_resolved == False
                ).first()
                if not existing:
                    alert = tools.create_alert(
                        title=f"🔍 Possible duplicate charge at {merchant}",
                        message=f"Detected {len(exp_list)} transactions of ₹{amt:,.2f} at {merchant} within the last 7 days. Please verify this wasn't a duplicate billing.",
                        alert_type="anomaly",
                        severity="medium",
                        expense_id=exp_list[-1].id
                    )
                    generated_alerts.append(alert)

        return generated_alerts

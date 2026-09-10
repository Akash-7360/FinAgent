import time
from typing import Dict, Any, List, Optional
from datetime import date, datetime, timedelta
import calendar
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from backend.app.models.entities import (
    Expense, Budget, Alert, AgentEvent, UserPreference, MonthlyReport, RecurringExpense
)
from backend.app.agent.memory import PersonalizedMemory, compute_text_embedding
from ml.anomaly_detector import MultiLayerAnomalyDetector

class AgentTools:
    """Implements the 14 dynamic tool capabilities executable by the agent."""

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
        self.memory = PersonalizedMemory(db, user_id)

    # 1. add_expense
    def add_expense(
        self,
        amount: float,
        merchant: str,
        category: str,
        subcategory: Optional[str] = None,
        description: Optional[str] = None,
        date_str: Optional[str] = None,
        payment_method: str = "Card",
        confidence_score: float = 1.0,
        categorization_reason: Optional[str] = None,
        is_anomaly: bool = False,
        anomaly_score: float = 0.0,
        anomaly_reason: Optional[str] = None,
        is_recurring: bool = False
    ) -> Dict[str, Any]:
        exp_date = date.fromisoformat(date_str) if date_str else date.today()
        embedding = compute_text_embedding(f"{merchant} {category} {subcategory or ''} {description or ''}")

        expense = Expense(
            user_id=self.user_id,
            amount=amount,
            merchant=merchant,
            category=category,
            subcategory=subcategory,
            description=description,
            date=exp_date,
            payment_method=payment_method,
            confidence_score=confidence_score,
            categorization_reason=categorization_reason,
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            anomaly_reason=anomaly_reason,
            is_recurring=is_recurring,
            embedding=embedding
        )
        self.db.add(expense)
        self.db.commit()
        self.db.refresh(expense)

        return {
            "id": expense.id,
            "amount": float(expense.amount),
            "merchant": expense.merchant,
            "category": expense.category,
            "subcategory": expense.subcategory,
            "date": expense.date.isoformat(),
            "is_anomaly": expense.is_anomaly,
            "anomaly_score": float(expense.anomaly_score),
            "message": f"Successfully logged expense of ₹{expense.amount:,.2f} at {expense.merchant}."
        }

    # 2. get_expense_history
    def get_expense_history(
        self,
        category: Optional[str] = None,
        merchant: Optional[str] = None,
        limit: int = 20,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        q = self.db.query(Expense).filter(Expense.user_id == self.user_id)
        if category:
            q = q.filter(Expense.category == category)
        if merchant:
            q = q.filter(Expense.merchant.ilike(f"%{merchant}%"))
        if start_date:
            q = q.filter(Expense.date >= date.fromisoformat(start_date))
        if end_date:
            q = q.filter(Expense.date <= date.fromisoformat(end_date))

        expenses = q.order_by(Expense.date.desc()).limit(limit).all()
        return [
            {
                "id": e.id,
                "amount": float(e.amount),
                "merchant": e.merchant,
                "category": e.category,
                "subcategory": e.subcategory,
                "description": e.description,
                "date": e.date.isoformat(),
                "is_anomaly": e.is_anomaly,
                "anomaly_score": float(e.anomaly_score)
            }
            for e in expenses
        ]

    # 3. get_category_spending
    def get_category_spending(
        self,
        category: str,
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        today = date.today()
        m = month or today.month
        y = year or today.year

        expenses = self.db.query(Expense).filter(
            Expense.user_id == self.user_id,
            Expense.category == category,
            extract('month', Expense.date) == m,
            extract('year', Expense.date) == y
        ).all()

        total = sum(float(e.amount) for e in expenses)
        count = len(expenses)
        avg = (total / count) if count > 0 else 0.0

        return {
            "category": category,
            "month": m,
            "year": y,
            "total_spending": round(total, 2),
            "transaction_count": count,
            "average_transaction": round(avg, 2)
        }

    # 4. get_monthly_spending
    def get_monthly_spending(self, months_back: int = 6) -> List[Dict[str, Any]]:
        today = date.today()
        results = []
        for i in range(months_back - 1, -1, -1):
            # Calculate target month/year
            target_date = today.replace(day=1) - timedelta(days=i * 28)
            m = target_date.month
            y = target_date.year

            total = self.db.query(func.sum(Expense.amount)).filter(
                Expense.user_id == self.user_id,
                extract('month', Expense.date) == m,
                extract('year', Expense.date) == y
            ).scalar() or 0.0

            count = self.db.query(func.count(Expense.id)).filter(
                Expense.user_id == self.user_id,
                extract('month', Expense.date) == m,
                extract('year', Expense.date) == y
            ).scalar() or 0

            month_name = calendar.month_abbr[m]
            results.append({
                "month_name": f"{month_name} {y}",
                "month": m,
                "year": y,
                "total_amount": round(float(total), 2),
                "transaction_count": count
            })
        return results

    # 5. get_merchant_history
    def get_merchant_history(self, merchant: str) -> Dict[str, Any]:
        expenses = self.db.query(Expense).filter(
            Expense.user_id == self.user_id,
            Expense.merchant.ilike(f"%{merchant}%")
        ).order_by(Expense.date.desc()).all()

        if not expenses:
            return {
                "merchant": merchant,
                "total_spent": 0.0,
                "count": 0,
                "average": 0.0,
                "recent_transactions": []
            }

        amounts = [float(e.amount) for e in expenses]
        return {
            "merchant": merchant,
            "total_spent": round(sum(amounts), 2),
            "count": len(amounts),
            "average": round(float(np.mean(amounts)), 2),
            "min": round(min(amounts), 2),
            "max": round(max(amounts), 2),
            "recent_transactions": [
                {"id": e.id, "amount": float(e.amount), "date": e.date.isoformat(), "category": e.category}
                for e in expenses[:5]
            ]
        }

    # 6. search_similar_transactions
    def search_similar_transactions(
        self,
        merchant_or_desc: str,
        category: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        return self.memory.search_similar_transactions(merchant_or_desc, category=category, limit=limit)

    # 7. check_budget
    def check_budget(self, category: str) -> Dict[str, Any]:
        today = date.today()
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        days_remaining = max(1, days_in_month - today.day)
        day_ratio = today.day / float(days_in_month)

        budget = self.db.query(Budget).filter(
            Budget.user_id == self.user_id,
            Budget.category == category
        ).first()

        spent = self.db.query(func.sum(Expense.amount)).filter(
            Expense.user_id == self.user_id,
            Expense.category == category,
            extract('month', Expense.date) == today.month,
            extract('year', Expense.date) == today.year
        ).scalar() or 0.0
        spent = float(spent)

        if not budget:
            return {
                "has_budget": False,
                "category": category,
                "spent_so_far": round(spent, 2),
                "monthly_limit": None,
                "remaining_amount": None,
                "percentage_used": None,
                "is_exceeded": False,
                "projected_spend": round((spent / max(1, today.day)) * days_in_month, 2),
                "recommendation": f"No active budget defined for {category}. Consider creating one to maintain control."
            }

        limit = float(budget.monthly_limit)
        remaining = limit - spent
        percentage = (spent / limit) * 100.0 if limit > 0 else 100.0
        projected = (spent / max(1, today.day)) * days_in_month

        # Velocity check: is spending pacing ahead of the month's progression?
        is_exceeded = spent >= limit
        is_warning = (percentage / 100.0) >= float(budget.alert_threshold) or (projected > limit)

        status = "exceeded" if is_exceeded else ("warning" if is_warning else "safe")

        recommendation = ""
        if is_exceeded:
            recommendation = f"You have exceeded your {category} budget by ₹{abs(remaining):,.2f}."
        elif is_warning:
            daily_allowance = remaining / days_remaining
            recommendation = f"At your current velocity, you are projected to reach ₹{projected:,.0f} (budget is ₹{limit:,.0f}). Limit further {category} spending to ~₹{daily_allowance:,.0f}/day for the remaining {days_remaining} days."
        else:
            recommendation = f"Your {category} spending is healthy with ₹{remaining:,.2f} remaining."

        return {
            "has_budget": True,
            "category": category,
            "monthly_limit": round(limit, 2),
            "spent_so_far": round(spent, 2),
            "remaining_amount": round(remaining, 2),
            "percentage_used": round(percentage, 1),
            "is_exceeded": is_exceeded,
            "status": status,
            "days_remaining": days_remaining,
            "projected_spend": round(projected, 2),
            "recommendation": recommendation
        }

    # 8. create_budget
    def create_budget(
        self,
        category: str,
        monthly_limit: float,
        alert_threshold: float = 0.80
    ) -> Dict[str, Any]:
        existing = self.db.query(Budget).filter(
            Budget.user_id == self.user_id,
            Budget.category == category
        ).first()

        if existing:
            existing.monthly_limit = monthly_limit
            existing.alert_threshold = alert_threshold
            self.db.commit()
            self.db.refresh(existing)
            return {"status": "updated", "category": category, "monthly_limit": monthly_limit}

        budget = Budget(
            user_id=self.user_id,
            category=category,
            monthly_limit=monthly_limit,
            alert_threshold=alert_threshold
        )
        self.db.add(budget)
        self.db.commit()
        self.db.refresh(budget)
        return {"status": "created", "category": category, "monthly_limit": monthly_limit}

    # 9. update_budget
    def update_budget(
        self,
        category: str,
        monthly_limit: Optional[float] = None,
        alert_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        budget = self.db.query(Budget).filter(
            Budget.user_id == self.user_id,
            Budget.category == category
        ).first()
        if not budget:
            return {"status": "not_found", "message": f"No budget found for category {category}."}

        if monthly_limit is not None:
            budget.monthly_limit = monthly_limit
        if alert_threshold is not None:
            budget.alert_threshold = alert_threshold

        self.db.commit()
        self.db.refresh(budget)
        return {
            "status": "updated",
            "category": category,
            "monthly_limit": float(budget.monthly_limit),
            "alert_threshold": float(budget.alert_threshold)
        }

    # 10. detect_anomaly
    def detect_anomaly(
        self,
        amount: float,
        category: str,
        merchant: str,
        date_str: Optional[str] = None
    ) -> Dict[str, Any]:
        prefs = self.get_user_preferences()
        sensitivity = prefs.get("anomaly_sensitivity", 0.70)
        detector = MultiLayerAnomalyDetector(sensitivity=sensitivity)

        # Retrieve user historical expenses
        history = self.db.query(Expense).filter(Expense.user_id == self.user_id).all()
        hist_dicts = [
            {
                "amount": float(e.amount),
                "category": e.category,
                "merchant": e.merchant,
                "date": e.date.isoformat()
            }
            for e in history
        ]

        target = {
            "amount": amount,
            "category": category,
            "merchant": merchant,
            "date": date_str or date.today().isoformat()
        }

        res = detector.detect(target, hist_dicts)
        return res.to_dict()

    # 11. calculate_spending_trend
    def calculate_spending_trend(self, category: Optional[str] = None) -> Dict[str, Any]:
        today = date.today()
        # Current month
        m_curr = today.month
        y_curr = today.year
        # Last month
        last_m_date = today.replace(day=1) - timedelta(days=1)
        m_prev = last_m_date.month
        y_prev = last_m_date.year

        curr_q = self.db.query(func.sum(Expense.amount)).filter(
            Expense.user_id == self.user_id,
            extract('month', Expense.date) == m_curr,
            extract('year', Expense.date) == y_curr
        )
        prev_q = self.db.query(func.sum(Expense.amount)).filter(
            Expense.user_id == self.user_id,
            extract('month', Expense.date) == m_prev,
            extract('year', Expense.date) == y_prev
        )

        if category:
            curr_q = curr_q.filter(Expense.category == category)
            prev_q = prev_q.filter(Expense.category == category)

        curr_spent = float(curr_q.scalar() or 0.0)
        prev_spent = float(prev_q.scalar() or 0.0)

        diff = curr_spent - prev_spent
        percent_change = ((diff / prev_spent) * 100.0) if prev_spent > 0 else (100.0 if curr_spent > 0 else 0.0)

        direction = "increased" if diff > 0 else ("decreased" if diff < 0 else "unchanged")
        label = f"{category} spending" if category else "Overall spending"

        trend_explanation = (
            f"{label} {direction} by {abs(round(percent_change, 1))}% compared to last month "
            f"(₹{curr_spent:,.0f} vs ₹{prev_spent:,.0f})."
        )

        return {
            "category": category or "All",
            "current_month_spent": round(curr_spent, 2),
            "previous_month_spent": round(prev_spent, 2),
            "difference": round(diff, 2),
            "percentage_change": round(percent_change, 1),
            "direction": direction,
            "explanation": trend_explanation
        }

    # 12. generate_monthly_report
    def generate_monthly_report(self, month: Optional[int] = None, year: Optional[int] = None) -> Dict[str, Any]:
        today = date.today()
        m = month or today.month
        y = year or today.year

        expenses = self.db.query(Expense).filter(
            Expense.user_id == self.user_id,
            extract('month', Expense.date) == m,
            extract('year', Expense.date) == y
        ).order_by(Expense.amount.desc()).all()

        total_spent = sum(float(e.amount) for e in expenses)

        cat_breakdown: Dict[str, float] = {}
        for e in expenses:
            cat_breakdown[e.category] = cat_breakdown.get(e.category, 0.0) + float(e.amount)

        # Top 5 expenses
        top_expenses = [
            {
                "id": e.id,
                "amount": float(e.amount),
                "merchant": e.merchant,
                "category": e.category,
                "date": e.date.isoformat(),
                "is_anomaly": e.is_anomaly
            }
            for e in expenses[:5]
        ]

        anomaly_count = sum(1 for e in expenses if e.is_anomaly)

        # Budgets adherence
        budgets = self.db.query(Budget).filter(Budget.user_id == self.user_id).all()
        budget_adherence = {}
        for b in budgets:
            c_spent = cat_breakdown.get(b.category, 0.0)
            budget_adherence[b.category] = {
                "limit": float(b.monthly_limit),
                "spent": round(c_spent, 2),
                "status": "Exceeded" if c_spent > float(b.monthly_limit) else "Within Budget"
            }

        # Recommendations & AI summary
        top_cat = max(cat_breakdown.items(), key=lambda x: x[1])[0] if cat_breakdown else "None"
        ai_summary = (
            f"In {calendar.month_name[m]} {y}, your total expenditure was ₹{total_spent:,.2f}. "
            f"The largest category was '{top_cat}' with ₹{cat_breakdown.get(top_cat, 0.0):,.2f}. "
            f"{anomaly_count} anomalous spending incidents were flagged."
        )

        recommendations = [
            f"Review your high spending in {top_cat} to identify non-essential discretionary expenses.",
            "Consider setting tighter budget alert thresholds for categories nearing 90% utilization.",
            "Schedule recurring reviews for subscriptions that have increased over the last quarter."
        ]

        # Save or update report in DB
        rep = self.db.query(MonthlyReport).filter(
            MonthlyReport.user_id == self.user_id,
            MonthlyReport.month == m,
            MonthlyReport.year == y
        ).first()

        if not rep:
            rep = MonthlyReport(
                user_id=self.user_id,
                month=m,
                year=y,
                total_spent=total_spent,
                category_breakdown=cat_breakdown,
                top_expenses=top_expenses,
                anomaly_count=anomaly_count,
                budget_adherence=budget_adherence,
                ai_summary=ai_summary,
                recommendations=recommendations
            )
            self.db.add(rep)
        else:
            rep.total_spent = total_spent
            rep.category_breakdown = cat_breakdown
            rep.top_expenses = top_expenses
            rep.anomaly_count = anomaly_count
            rep.budget_adherence = budget_adherence
            rep.ai_summary = ai_summary
            rep.recommendations = recommendations

        self.db.commit()

        return {
            "month": m,
            "year": y,
            "month_name": f"{calendar.month_name[m]} {y}",
            "total_spent": round(total_spent, 2),
            "category_breakdown": {k: round(v, 2) for k, v in cat_breakdown.items()},
            "top_expenses": top_expenses,
            "anomaly_count": anomaly_count,
            "budget_adherence": budget_adherence,
            "ai_summary": ai_summary,
            "recommendations": recommendations
        }

    # 13. create_alert
    def create_alert(
        self,
        title: str,
        message: str,
        alert_type: str = "anomaly",
        severity: str = "medium",
        expense_id: Optional[str] = None
    ) -> Dict[str, Any]:
        alert = Alert(
            user_id=self.user_id,
            title=title,
            message=message,
            alert_type=alert_type,
            severity=severity,
            expense_id=expense_id,
            is_resolved=False
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return {
            "id": alert.id,
            "title": alert.title,
            "message": alert.message,
            "severity": alert.severity,
            "created_at": alert.created_at.isoformat()
        }

    # 14. get_user_preferences
    def get_user_preferences(self) -> Dict[str, Any]:
        pref = self.db.query(UserPreference).filter(UserPreference.user_id == self.user_id).first()
        if not pref:
            return {
                "confidence_threshold": 0.75,
                "anomaly_sensitivity": 0.70,
                "budget_alert_threshold": 0.80,
                "enable_proactive_alerts": True,
                "dark_mode": True
            }
        return {
            "confidence_threshold": float(pref.confidence_threshold),
            "anomaly_sensitivity": float(pref.anomaly_sensitivity),
            "budget_alert_threshold": float(pref.budget_alert_threshold),
            "enable_proactive_alerts": pref.enable_proactive_alerts,
            "dark_mode": pref.dark_mode
        }

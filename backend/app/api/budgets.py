from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.entities import Budget, User
from backend.app.schemas.schemas import BudgetCreate, BudgetUpdate, BudgetResponse
from backend.app.api.deps import get_current_user
from backend.app.agent.tools import AgentTools

router = APIRouter(prefix="/budgets", tags=["budgets"])

@router.get("", response_model=List[BudgetResponse])
def list_budgets(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tools = AgentTools(db, user.id)
    budgets = db.query(Budget).filter(Budget.user_id == user.id).all()
    results = []

    for b in budgets:
        check = tools.check_budget(b.category)
        spent = check.get("spent_so_far", 0.0)
        rem = check.get("remaining_amount", float(b.monthly_limit))
        pct = check.get("percentage_used", 0.0)
        proj = check.get("projected_spend", spent)
        status_val = check.get("status", "safe")

        results.append(BudgetResponse(
            id=b.id,
            user_id=b.user_id,
            category=b.category,
            monthly_limit=float(b.monthly_limit),
            alert_threshold=float(b.alert_threshold),
            period=b.period,
            spent_so_far=spent,
            remaining_amount=rem,
            percentage_used=pct,
            is_exceeded=check.get("is_exceeded", False),
            projected_spend=proj,
            velocity_status=status_val,
            created_at=b.created_at
        ))

    return results

@router.post("", response_model=BudgetResponse)
def create_budget(
    budget_in: BudgetCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(Budget).filter(
        Budget.user_id == user.id,
        Budget.category == budget_in.category
    ).first()

    if existing:
        existing.monthly_limit = budget_in.monthly_limit
        existing.alert_threshold = budget_in.alert_threshold or 0.80
        db.commit()
        db.refresh(existing)
        b = existing
    else:
        b = Budget(
            user_id=user.id,
            category=budget_in.category,
            monthly_limit=budget_in.monthly_limit,
            alert_threshold=budget_in.alert_threshold or 0.80,
            period=budget_in.period or "monthly"
        )
        db.add(b)
        db.commit()
        db.refresh(b)

    tools = AgentTools(db, user.id)
    check = tools.check_budget(b.category)
    return BudgetResponse(
        id=b.id,
        user_id=b.user_id,
        category=b.category,
        monthly_limit=float(b.monthly_limit),
        alert_threshold=float(b.alert_threshold),
        period=b.period,
        spent_so_far=check.get("spent_so_far", 0.0),
        remaining_amount=check.get("remaining_amount", float(b.monthly_limit)),
        percentage_used=check.get("percentage_used", 0.0),
        is_exceeded=check.get("is_exceeded", False),
        projected_spend=check.get("projected_spend", 0.0),
        velocity_status=check.get("status", "safe"),
        created_at=b.created_at
    )

@router.put("/{id}", response_model=BudgetResponse)
def update_budget(
    id: str,
    budget_in: BudgetUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    b = db.query(Budget).filter(Budget.id == id, Budget.user_id == user.id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Budget not found")

    if budget_in.monthly_limit is not None:
        b.monthly_limit = budget_in.monthly_limit
    if budget_in.alert_threshold is not None:
        b.alert_threshold = budget_in.alert_threshold

    db.commit()
    db.refresh(b)

    tools = AgentTools(db, user.id)
    check = tools.check_budget(b.category)
    return BudgetResponse(
        id=b.id,
        user_id=b.user_id,
        category=b.category,
        monthly_limit=float(b.monthly_limit),
        alert_threshold=float(b.alert_threshold),
        period=b.period,
        spent_so_far=check.get("spent_so_far", 0.0),
        remaining_amount=check.get("remaining_amount", float(b.monthly_limit)),
        percentage_used=check.get("percentage_used", 0.0),
        is_exceeded=check.get("is_exceeded", False),
        projected_spend=check.get("projected_spend", 0.0),
        velocity_status=check.get("status", "safe"),
        created_at=b.created_at
    )

@router.delete("/{id}")
def delete_budget(
    id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    b = db.query(Budget).filter(Budget.id == id, Budget.user_id == user.id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Budget not found")
    db.delete(b)
    db.commit()
    return {"message": "Budget deleted successfully"}

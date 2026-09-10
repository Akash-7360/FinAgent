import csv
import io
import re
from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.entities import Expense, User
from backend.app.schemas.schemas import ExpenseCreate, ExpenseUpdate, ExpenseResponse
from backend.app.api.deps import get_current_user
from backend.app.agent.tools import AgentTools
from backend.app.agent.categorizer import CategorizationEngine

router = APIRouter(prefix="/expenses", tags=["expenses"])

@router.get("", response_model=List[ExpenseResponse])
def list_expenses(
    category: Optional[str] = None,
    merchant: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    is_anomaly: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(Expense).filter(Expense.user_id == user.id)
    if category and category != "All":
        q = q.filter(Expense.category == category)
    if merchant:
        q = q.filter(Expense.merchant.ilike(f"%{merchant}%"))
    if start_date:
        q = q.filter(Expense.date >= start_date)
    if end_date:
        q = q.filter(Expense.date <= end_date)
    if is_anomaly is not None:
        q = q.filter(Expense.is_anomaly == is_anomaly)

    expenses = q.order_by(Expense.date.desc(), Expense.created_at.desc()).offset(offset).limit(limit).all()
    return expenses

@router.get("/{id}", response_model=ExpenseResponse)
def get_expense(
    id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    expense = db.query(Expense).filter(Expense.id == id, Expense.user_id == user.id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense

@router.post("", response_model=ExpenseResponse)
def create_expense(
    expense_in: ExpenseCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tools = AgentTools(db, user.id)
    categorizer = CategorizationEngine()

    category = expense_in.category
    subcategory = expense_in.subcategory
    confidence = expense_in.confidence_score or 1.0
    reason = expense_in.categorization_reason

    # Auto-categorize if not provided
    if not category or category == "Other":
        cat_res = categorizer.categorize(expense_in.merchant, amount=expense_in.amount, description=expense_in.description)
        category = cat_res["category"]
        subcategory = cat_res.get("subcategory")
        confidence = cat_res["confidence_score"]
        reason = cat_res["reason"]

    # Run Anomaly Detection Layer
    anom_res = tools.detect_anomaly(
        amount=expense_in.amount,
        category=category,
        merchant=expense_in.merchant,
        date_str=expense_in.date.isoformat() if expense_in.date else None
    )

    created = tools.add_expense(
        amount=expense_in.amount,
        merchant=expense_in.merchant,
        category=category,
        subcategory=subcategory,
        description=expense_in.description,
        date_str=expense_in.date.isoformat() if expense_in.date else None,
        payment_method=expense_in.payment_method or "Card",
        confidence_score=confidence,
        categorization_reason=reason,
        is_anomaly=anom_res["is_anomaly"],
        anomaly_score=anom_res["anomaly_score"],
        anomaly_reason=anom_res["reason"],
        is_recurring=expense_in.is_recurring or False
    )

    # If anomaly, proactively create alert
    if anom_res["is_anomaly"]:
        tools.create_alert(
            title=f"⚠️ Unusual spending: ₹{expense_in.amount:,.0f} at {expense_in.merchant}",
            message=f"Transaction flagged by anomaly engine. {anom_res['reason']}",
            alert_type="anomaly",
            severity="high" if anom_res["anomaly_score"] >= 0.85 else "medium",
            expense_id=created["id"]
        )

    # Return refreshed DB model
    return db.query(Expense).filter(Expense.id == created["id"]).first()

@router.delete("/{id}")
def delete_expense(
    id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    expense = db.query(Expense).filter(Expense.id == id, Expense.user_id == user.id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(expense)
    db.commit()
    return {"message": "Expense deleted successfully"}

# -----------------------------------------------------------------------------
# SMART CSV IMPORT WITH FUZZY COLUMN MAPPING LAYER
# -----------------------------------------------------------------------------
@router.post("/import")
async def import_expenses_csv(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Imports CSV transactions using flexible fuzzy column mapping.
    Maps amount/price, merchant/payee, date/time, category, payment_method.
    Automatically routes each transaction through the agent categorizer & anomaly pipeline.
    """
    if not file.filename.endswith(('.csv', '.txt')):
        raise HTTPException(status_code=400, detail="File must be a CSV format.")

    content = await file.read()
    try:
        decoded = content.decode('utf-8')
    except UnicodeDecodeError:
        decoded = content.decode('latin-1')

    reader = csv.DictReader(io.StringIO(decoded))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="Empty or invalid CSV file.")

    # Column name mapping heuristics
    headers = {h.strip().lower(): h for h in reader.fieldnames}

    def find_col(candidates):
        for c in candidates:
            for h_lower, orig in headers.items():
                if c in h_lower:
                    return orig
        return None

    amount_col = find_col(["amount", "price", "cost", "total", "spent", "debit", "value"])
    merchant_col = find_col(["merchant", "payee", "description", "name", "vendor", "store", "to"])
    date_col = find_col(["date", "time", "day", "transaction_date"])
    category_col = find_col(["category", "type", "tag"])
    payment_col = find_col(["payment_method", "payment", "mode", "account", "card"])

    if not amount_col:
        raise HTTPException(
            status_code=400,
            detail=f"Could not identify an Amount column in headers: {reader.fieldnames}"
        )

    tools = AgentTools(db, user.id)
    categorizer = CategorizationEngine()
    imported_count = 0
    anomalies_detected = 0

    for row in reader:
        try:
            raw_amt = str(row.get(amount_col, "")).replace("₹", "").replace("$", "").replace(",", "").strip()
            if not raw_amt:
                continue
            amt = abs(float(raw_amt))
            if amt == 0:
                continue

            merchant = (row.get(merchant_col) if merchant_col else "Unknown Merchant") or "Unknown Merchant"
            category = row.get(category_col) if category_col else None
            payment_method = row.get(payment_col) if payment_col else "Card"

            # Parse date safely
            trans_date = date.today()
            if date_col and row.get(date_col):
                raw_d = str(row.get(date_col)).strip()
                try:
                    trans_date = datetime.strptime(raw_d, "%Y-%m-%d").date()
                except ValueError:
                    try:
                        trans_date = datetime.strptime(raw_d, "%d/%m/%Y").date()
                    except ValueError:
                        try:
                            trans_date = datetime.strptime(raw_d, "%m/%d/%Y").date()
                        except ValueError:
                            trans_date = date.today()

            # Auto-categorize if missing
            subcategory = None
            conf = 1.0
            reason = "CSV Specified"
            if not category or category.strip() == "":
                cat_res = categorizer.categorize(merchant, amount=amt)
                category = cat_res["category"]
                subcategory = cat_res["subcategory"]
                conf = cat_res["confidence_score"]
                reason = cat_res["reason"]

            # Anomaly check
            anom = tools.detect_anomaly(amt, category, merchant, trans_date.isoformat())

            tools.add_expense(
                amount=amt,
                merchant=merchant,
                category=category,
                subcategory=subcategory,
                date_str=trans_date.isoformat(),
                payment_method=payment_method or "Card",
                confidence_score=conf,
                categorization_reason=reason,
                is_anomaly=anom["is_anomaly"],
                anomaly_score=anom["anomaly_score"],
                anomaly_reason=anom["reason"]
            )
            imported_count += 1
            if anom["is_anomaly"]:
                anomalies_detected += 1

        except Exception as e:
            continue

    return {
        "message": f"Successfully processed CSV file.",
        "imported_count": imported_count,
        "anomalies_detected": anomalies_detected,
        "detected_columns": {
            "amount": amount_col,
            "merchant": merchant_col,
            "date": date_col,
            "category": category_col
        }
    }

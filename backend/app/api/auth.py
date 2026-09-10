from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import hash_password, verify_password, create_access_token
from backend.app.models.entities import User, UserPreference
from backend.app.schemas.schemas import (
    UserCreate, UserLogin, Token, UserResponse, UserPreferenceUpdate, UserPreferenceResponse
)
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=Token)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        currency=user_in.currency or "₹",
        monthly_income=user_in.monthly_income or 0.0
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Initialize default user preferences
    pref = UserPreference(
        user_id=user.id,
        confidence_threshold=0.75,
        anomaly_sensitivity=0.70,
        budget_alert_threshold=0.80,
        enable_proactive_alerts=True,
        dark_mode=True
    )
    db.add(pref)
    db.commit()

    token = create_access_token({"sub": user.id, "email": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "currency": user.currency
        }
    }

@router.post("/login", response_model=Token)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_in.email).first()
    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    token = create_access_token({"sub": user.id, "email": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "currency": user.currency
        }
    }

@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    return user

@router.put("/preferences", response_model=UserPreferenceResponse)
def update_preferences(
    pref_in: UserPreferenceUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pref = db.query(UserPreference).filter(UserPreference.user_id == user.id).first()
    if not pref:
        pref = UserPreference(user_id=user.id)
        db.add(pref)

    if pref_in.confidence_threshold is not None:
        pref.confidence_threshold = pref_in.confidence_threshold
    if pref_in.anomaly_sensitivity is not None:
        pref.anomaly_sensitivity = pref_in.anomaly_sensitivity
    if pref_in.budget_alert_threshold is not None:
        pref.budget_alert_threshold = pref_in.budget_alert_threshold
    if pref_in.enable_proactive_alerts is not None:
        pref.enable_proactive_alerts = pref_in.enable_proactive_alerts
    if pref_in.dark_mode is not None:
        pref.dark_mode = pref_in.dark_mode

    db.commit()
    db.refresh(pref)
    return pref

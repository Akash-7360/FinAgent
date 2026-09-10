from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.entities import AgentEvent, User
from backend.app.schemas.schemas import (
    AgentChatRequest, AgentChatResponse, AgentAnalyzeRequest, AgentEventResponse
)
from backend.app.api.deps import get_current_user
from backend.app.agent.orchestrator import AgentOrchestrator
from backend.app.agent.proactive import ProactiveMonitor

router = APIRouter(prefix="/agent", tags=["agent"])

@router.post("/chat", response_model=AgentChatResponse)
def chat_with_agent(
    req: AgentChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    orchestrator = AgentOrchestrator(db, user.id)
    result = orchestrator.run(req.message, context=req.context)
    return AgentChatResponse(**result)

@router.post("/analyze")
def analyze_text(
    req: AgentAnalyzeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    orchestrator = AgentOrchestrator(db, user.id)
    # Run perception and confidence nodes
    state = orchestrator.graph.invoke({
        "user_id": user.id,
        "input_text": req.text,
        "intent": "",
        "extracted_entities": {},
        "categorization": {},
        "requires_clarification": False,
        "clarification_prompt": None,
        "suggested_categories": [],
        "planned_tools": [],
        "executed_tools": [],
        "tool_results": {},
        "anomaly_data": None,
        "budget_data": None,
        "created_expense": None,
        "created_alert": None,
        "insights": [],
        "final_response": ""
    })
    return {
        "extracted_entities": state.get("extracted_entities"),
        "categorization": state.get("categorization"),
        "requires_clarification": state.get("requires_clarification"),
        "clarification_prompt": state.get("clarification_prompt"),
        "suggested_categories": state.get("suggested_categories")
    }

@router.get("/events", response_model=List[AgentEventResponse])
def get_agent_events(
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    events = db.query(AgentEvent).filter(
        AgentEvent.user_id == user.id
    ).order_by(AgentEvent.timestamp.desc()).offset(offset).limit(limit).all()
    return events

@router.post("/proactive/trigger")
def trigger_proactive_scan(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    monitor = ProactiveMonitor(db)
    alerts = monitor.scan_user(user.id)
    return {
        "message": f"Autonomous scan complete. {len(alerts)} alerts generated.",
        "alerts_generated": len(alerts)
    }

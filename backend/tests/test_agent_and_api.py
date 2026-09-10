from datetime import date
from backend.app.core.database import SessionLocal
from backend.app.models.entities import User
from backend.app.agent.orchestrator import AgentOrchestrator
from backend.app.agent.tools import AgentTools
from ml.anomaly_detector import MultiLayerAnomalyDetector

def test_anomaly_detector_3_layers():
    detector = MultiLayerAnomalyDetector(sensitivity=0.70)
    history = [
        {"amount": 450, "category": "Food", "merchant": "Swiggy", "date": "2026-09-01"},
        {"amount": 520, "category": "Food", "merchant": "Subway", "date": "2026-09-02"},
        {"amount": 650, "category": "Food", "merchant": "Chai Point", "date": "2026-09-03"},
        {"amount": 700, "category": "Food", "merchant": "McDonalds", "date": "2026-09-04"},
        {"amount": 850, "category": "Food", "merchant": "Dominos", "date": "2026-09-05"},
        {"amount": 600, "category": "Food", "merchant": "Swiggy", "date": "2026-09-06"},
        {"amount": 720, "category": "Food", "merchant": "KFC", "date": "2026-09-07"},
        {"amount": 550, "category": "Food", "merchant": "Cafe Coffee Day", "date": "2026-09-08"},
        {"amount": 680, "category": "Food", "merchant": "Swiggy", "date": "2026-09-09"},
        {"amount": 750, "category": "Food", "merchant": "Burger King", "date": "2026-09-10"},
    ]

    # Test 1: Normal dining transaction
    normal_res = detector.detect(
        {"amount": 650, "category": "Food", "merchant": "Subway", "date": "2026-09-11"},
        history
    )
    assert not normal_res.is_anomaly, "Normal ₹650 expense should not be flagged as anomaly"
    assert normal_res.anomaly_score < 0.50

    # Test 2: High value spike (₹4,500 restaurant dinner)
    spike_res = detector.detect(
        {"amount": 4500, "category": "Food", "merchant": "Bastian Restaurant", "date": "2026-09-11"},
        history
    )
    assert spike_res.is_anomaly, "High value ₹4,500 dinner should be flagged as anomaly"
    assert spike_res.anomaly_score >= 0.70
    assert "layer_results" in spike_res.to_dict()
    assert spike_res.layer_results["active_layers_concurring"] >= 2
    print("✓ Anomaly detector 3-layer test passed.")

def test_agent_clarification_on_ambiguous_payment():
    db = SessionLocal()
    user = db.query(User).filter(User.email == "demo@finagent.ai").first()
    orchestrator = AgentOrchestrator(db, user.id)

    # Test ambiguous peer transfer without clear purpose
    res = orchestrator.run("Paid ₹2,500 to Rahul")
    assert res["requires_clarification"] is True
    assert "Rahul" in res["clarification_prompt"]
    print("✓ Agent clarification test passed:", res["clarification_prompt"])
    db.close()

def test_agent_expense_addition_and_tools():
    db = SessionLocal()
    user = db.query(User).filter(User.email == "demo@finagent.ai").first()
    orchestrator = AgentOrchestrator(db, user.id)

    # Test Section 23 Demo Scenario: "₹4,500 — Restaurant — Today"
    res = orchestrator.run("₹4,500 — Restaurant — Today")
    assert not res["requires_clarification"]
    assert len(res["tools_executed"]) > 0
    tool_names = [t["tool_name"] for t in res["tools_executed"]]
    assert "detect_anomaly" in tool_names
    assert "add_expense" in tool_names
    assert res["created_alert"] is not None
    print("✓ Agent add expense and proactive alert test passed. Tools executed:", tool_names)
    db.close()

def test_agent_spending_inquiry():
    db = SessionLocal()
    user = db.query(User).filter(User.email == "demo@finagent.ai").first()
    orchestrator = AgentOrchestrator(db, user.id)

    # Test user query: "Am I spending too much on food?"
    res = orchestrator.run("Am I spending too much on food?")
    assert not res["requires_clarification"]
    assert len(res["tools_executed"]) > 0
    assert "Food" in res["response"] or "food" in res["response"].lower()
    print("✓ Agent inquiry test passed. Response excerpt:\n", res["response"][:150])
    db.close()

if __name__ == "__main__":
    test_anomaly_detector_3_layers()
    test_agent_clarification_on_ambiguous_payment()
    test_agent_expense_addition_and_tools()
    test_agent_spending_inquiry()
    print("\n🎉 All agent and ML tests executed successfully!")

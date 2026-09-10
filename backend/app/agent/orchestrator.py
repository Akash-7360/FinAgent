import re
import time
from typing import Dict, Any, List, Optional, TypedDict
from datetime import date, datetime, timezone
from sqlalchemy.orm import Session

from langgraph.graph import StateGraph, END, START
from backend.app.agent.tools import AgentTools
from backend.app.agent.categorizer import CategorizationEngine
from backend.app.models.entities import AgentEvent

class AgentState(TypedDict):
    user_id: str
    input_text: str
    intent: str
    extracted_entities: Dict[str, Any]
    categorization: Dict[str, Any]
    requires_clarification: bool
    clarification_prompt: Optional[str]
    suggested_categories: List[str]
    planned_tools: List[str]
    executed_tools: List[Dict[str, Any]]
    tool_results: Dict[str, Any]
    anomaly_data: Optional[Dict[str, Any]]
    budget_data: Optional[Dict[str, Any]]
    created_expense: Optional[Dict[str, Any]]
    created_alert: Optional[Dict[str, Any]]
    insights: List[str]
    final_response: str

class AgentOrchestrator:
    """
    LangGraph-powered Autonomous Financial Agent Orchestrator.
    Executes Perception -> Reasoning -> Dynamic Tool Planning -> Tool Calling -> Observation -> Synthesis.
    """

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
        self.tools = AgentTools(db, user_id)
        self.categorizer = CategorizationEngine()
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(AgentState)

        # Add Nodes
        builder.add_node("perceive_input", self._node_perceive_input)
        builder.add_node("evaluate_confidence", self._node_evaluate_confidence)
        builder.add_node("handle_clarification", self._node_handle_clarification)
        builder.add_node("plan_tools", self._node_plan_tools)
        builder.add_node("execute_tools", self._node_execute_tools)
        builder.add_node("observe_and_reason", self._node_observe_and_reason)
        builder.add_node("synthesize_and_audit", self._node_synthesize_and_audit)

        # Edges
        builder.add_edge(START, "perceive_input")
        builder.add_edge("perceive_input", "evaluate_confidence")

        # Conditional routing after confidence evaluation
        builder.add_conditional_edges(
            "evaluate_confidence",
            self._route_after_confidence,
            {
                "clarification": "handle_clarification",
                "proceed": "plan_tools"
            }
        )

        builder.add_edge("handle_clarification", "synthesize_and_audit")
        builder.add_edge("plan_tools", "execute_tools")
        builder.add_edge("execute_tools", "observe_and_reason")
        builder.add_edge("observe_and_reason", "synthesize_and_audit")
        builder.add_edge("synthesize_and_audit", END)

        return builder.compile()

    # -------------------------------------------------------------------------
    # ROUTING LOGIC
    # -------------------------------------------------------------------------
    def _route_after_confidence(self, state: AgentState) -> str:
        if state.get("requires_clarification", False):
            return "clarification"
        return "proceed"

    # -------------------------------------------------------------------------
    # NODE 1: PERCEIVE INPUT
    # -------------------------------------------------------------------------
    def _node_perceive_input(self, state: AgentState) -> Dict[str, Any]:
        text = state["input_text"].strip()
        lower = text.lower()

        # Extract amounts: ₹4,500, 4500, 4,500 INR, etc.
        amount = None
        amt_match = re.search(r'(?:₹|rs\.?|inr)?\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)', text, re.IGNORECASE)
        if amt_match:
            try:
                raw_amt = amt_match.group(1).replace(",", "")
                amount = float(raw_amt)
            except Exception:
                amount = None

        # Detect intent
        intent = "general_inquiry"
        if any(w in lower for w in ["spent", "paid", "bought", "purchase", "bill at", "ordered"]):
            intent = "add_expense"
        elif any(w in lower for w in ["am i spending too much", "spending too much", "how much did i spend", "spending trend", "category is costing me", "spending higher"]):
            intent = "spending_inquiry"
        elif any(w in lower for w in ["budget", "create a", "set budget", "limit for"]):
            intent = "budget_action"
        elif any(w in lower for w in ["unusual", "anomaly", "suspicious", "weird", "biggest expenses"]):
            intent = "anomaly_inquiry"
        elif any(w in lower for w in ["report", "monthly summary", "pdf"]):
            intent = "report_inquiry"
        elif any(w in lower for w in ["subscription", "recurring", "monthly bills"]):
            intent = "subscription_inquiry"
        elif amount is not None and len(text.split()) <= 6:
            # Short expense entry like "₹4,500 — Restaurant — Today" or "4500 restaurant"
            intent = "add_expense"

        # Extract merchant
        merchant = "Unknown"
        if intent == "add_expense":
            parts = [p.strip() for p in re.split(r'[—\-,|]', text) if p.strip()]
            if len(parts) >= 2:
                # E.g. "₹4,500 — Restaurant — Today"
                for p in parts:
                    if not re.search(r'^[0-9₹,\.]+$', p.replace("₹", "").strip()) and not any(t in p.lower() for t in ["today", "yesterday"]):
                        merchant = p.strip()
                        break
            else:
                m_match = re.search(r'(?:at|to|in|for)\s+([a-zA-Z0-9\s\'\.]+)', text, re.IGNORECASE)
                if m_match:
                    merchant = m_match.group(1).split()[0].capitalize()
                else:
                    words = [w for w in text.split() if not any(c.isdigit() for c in w) and w.lower() not in ["spent", "i", "at", "a", "the", "today", "yesterday", "paid"]]
                    if words:
                        merchant = " ".join(words[:2]).capitalize()

        return {
            "intent": intent,
            "extracted_entities": {
                "amount": amount,
                "merchant": merchant,
                "raw_text": text
            }
        }

    # -------------------------------------------------------------------------
    # NODE 2: EVALUATE CONFIDENCE
    # -------------------------------------------------------------------------
    def _node_evaluate_confidence(self, state: AgentState) -> Dict[str, Any]:
        text = state["input_text"]
        intent = state["intent"]
        entities = state.get("extracted_entities", {})
        merchant = entities.get("merchant", "")
        amount = entities.get("amount")

        # If it's an expense action, run categorization and check confidence
        if intent == "add_expense":
            cat_res = self.categorizer.categorize(merchant or text, amount=amount, description=text)
            if cat_res["needs_clarification"]:
                return {
                    "categorization": cat_res,
                    "requires_clarification": True,
                    "clarification_prompt": cat_res["clarification_prompt"],
                    "suggested_categories": cat_res["suggested_categories"]
                }
            return {
                "categorization": cat_res,
                "requires_clarification": False,
                "clarification_prompt": None,
                "suggested_categories": []
            }

        return {
            "categorization": {},
            "requires_clarification": False,
            "clarification_prompt": None,
            "suggested_categories": []
        }

    # -------------------------------------------------------------------------
    # NODE 3: HANDLE CLARIFICATION
    # -------------------------------------------------------------------------
    def _node_handle_clarification(self, state: AgentState) -> Dict[str, Any]:
        prompt = state.get("clarification_prompt") or "Could you clarify the category for this transaction?"
        self._log_event(
            agent_state="Awaiting_Clarification",
            decision="Triggered low-confidence clarification request to prevent incorrect transaction categorization",
            tool_called="categorize_transaction",
            tool_result_summary=f"Confidence {state['categorization'].get('confidence_score')}: below threshold."
        )
        return {
            "final_response": prompt,
            "insights": ["Confidence threshold check triggered: Pending user clarification before committing to database."]
        }

    # -------------------------------------------------------------------------
    # NODE 4: PLAN TOOLS
    # -------------------------------------------------------------------------
    def _node_plan_tools(self, state: AgentState) -> Dict[str, Any]:
        intent = state["intent"]
        tools_to_run = []

        if intent == "add_expense":
            # Real agentic multi-step workflow from prompt:
            # search_similar_transactions -> get_category_spending -> check_budget -> detect_anomaly -> add_expense -> create_alert (if anomaly)
            tools_to_run = [
                "search_similar_transactions",
                "get_category_spending",
                "check_budget",
                "detect_anomaly",
                "add_expense"
            ]
        elif intent == "spending_inquiry":
            tools_to_run = [
                "get_category_spending",
                "calculate_spending_trend",
                "check_budget",
                "get_monthly_spending"
            ]
        elif intent == "budget_action":
            tools_to_run = ["check_budget", "create_budget"]
        elif intent == "anomaly_inquiry":
            tools_to_run = ["get_expense_history", "calculate_spending_trend"]
        elif intent == "report_inquiry":
            tools_to_run = ["generate_monthly_report"]
        else:
            tools_to_run = ["get_monthly_spending", "get_user_preferences"]

        return {"planned_tools": tools_to_run}

    # -------------------------------------------------------------------------
    # NODE 5: EXECUTE TOOLS
    # -------------------------------------------------------------------------
    def _node_execute_tools(self, state: AgentState) -> Dict[str, Any]:
        executed = []
        results = {}
        entities = state.get("extracted_entities", {})
        cat_info = state.get("categorization", {})
        category = cat_info.get("category", "Food")
        amount = entities.get("amount", 0.0) or 0.0
        merchant = entities.get("merchant", "Restaurant")

        # Determine target category for spending inquiry if present in text
        text_lower = state["input_text"].lower()
        if state["intent"] == "spending_inquiry":
            for cat in ["food", "groceries", "transport", "shopping", "entertainment", "bills", "travel"]:
                if cat in text_lower:
                    category = cat.capitalize()
                    break

        for tool_name in state["planned_tools"]:
            start_t = time.time()
            res = None
            args = {}

            if tool_name == "search_similar_transactions":
                args = {"merchant_or_desc": merchant, "category": category, "limit": 3}
                res = self.tools.search_similar_transactions(**args)

            elif tool_name == "get_category_spending":
                args = {"category": category}
                res = self.tools.get_category_spending(**args)

            elif tool_name == "check_budget":
                args = {"category": category}
                res = self.tools.check_budget(**args)

            elif tool_name == "detect_anomaly":
                args = {"amount": amount, "category": category, "merchant": merchant}
                res = self.tools.detect_anomaly(**args)

            elif tool_name == "add_expense":
                # Check if anomaly was detected in previous step
                anom = results.get("detect_anomaly", {})
                is_anom = anom.get("is_anomaly", False)
                anom_score = anom.get("anomaly_score", 0.0)
                anom_reason = anom.get("reason", "")

                args = {
                    "amount": amount,
                    "merchant": merchant,
                    "category": category,
                    "subcategory": cat_info.get("subcategory"),
                    "description": state["input_text"],
                    "confidence_score": cat_info.get("confidence_score", 0.95),
                    "categorization_reason": cat_info.get("reason", ""),
                    "is_anomaly": is_anom,
                    "anomaly_score": anom_score,
                    "anomaly_reason": anom_reason
                }
                res = self.tools.add_expense(**args)

            elif tool_name == "calculate_spending_trend":
                args = {"category": category if category != "Other" else None}
                res = self.tools.calculate_spending_trend(**args)

            elif tool_name == "get_monthly_spending":
                args = {"months_back": 6}
                res = self.tools.get_monthly_spending(**args)

            elif tool_name == "get_expense_history":
                args = {"limit": 10}
                res = self.tools.get_expense_history(**args)

            elif tool_name == "generate_monthly_report":
                args = {}
                res = self.tools.generate_monthly_report(**args)

            elif tool_name == "get_user_preferences":
                args = {}
                res = self.tools.get_user_preferences()

            elif tool_name == "create_budget":
                args = {"category": category, "monthly_limit": amount or 5000.0}
                res = self.tools.create_budget(**args)

            duration_ms = int((time.time() - start_t) * 1000)
            results[tool_name] = res
            executed.append({
                "tool_name": tool_name,
                "arguments": args,
                "result": res,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            # Audit event logging
            self._log_event(
                agent_state="Tool_Execution",
                decision=f"Executed tool {tool_name}",
                tool_called=tool_name,
                tool_arguments=args,
                tool_result_summary=str(res)[:180],
                execution_time_ms=duration_ms
            )

        return {
            "executed_tools": executed,
            "tool_results": results,
            "anomaly_data": results.get("detect_anomaly"),
            "budget_data": results.get("check_budget"),
            "created_expense": results.get("add_expense")
        }

    # -------------------------------------------------------------------------
    # NODE 6: OBSERVE AND REASON
    # -------------------------------------------------------------------------
    def _node_observe_and_reason(self, state: AgentState) -> Dict[str, Any]:
        results = state["tool_results"]
        anom = results.get("detect_anomaly")
        budget = results.get("check_budget")
        created_exp = results.get("add_expense")
        created_alert = None
        insights = []

        # Autonomous proactive alert trigger: If anomaly detected or budget exceeded
        if anom and anom.get("is_anomaly"):
            exp_id = created_exp.get("id") if created_exp else None
            amt = created_exp.get("amount") if created_exp else state["extracted_entities"].get("amount", 0)
            merchant = created_exp.get("merchant") if created_exp else state["extracted_entities"].get("merchant", "")
            category = created_exp.get("category") if created_exp else "Expense"

            alert_title = f"⚠️ Unusual spending detected: ₹{amt:,.0f} at {merchant}"
            alert_msg = (
                f"You spent ₹{amt:,.0f} at {merchant}. "
                f"This is significantly higher than your typical {category} spending patterns. "
                f"Anomaly score: {anom.get('anomaly_score')}. Details: {anom.get('reason')}"
            )
            created_alert = self.tools.create_alert(
                title=alert_title,
                message=alert_msg,
                alert_type="anomaly",
                severity="high" if anom.get("anomaly_score", 0) >= 0.85 else "medium",
                expense_id=exp_id
            )
            insights.append(f"Autonomous Alert Generated: Unusual {category} spending detected.")

            self._log_event(
                agent_state="Autonomous_Alert_Triggered",
                decision=f"Generated high-priority alert for anomaly score {anom.get('anomaly_score')}",
                tool_called="create_alert",
                tool_result_summary=alert_title
            )

        # Budget observation
        if budget and budget.get("has_budget"):
            if budget.get("is_exceeded"):
                insights.append(f"Budget Exceeded: You have surpassed your {budget['category']} monthly budget by ₹{abs(budget['remaining_amount']):,.2f}.")
            elif budget.get("status") == "warning":
                insights.append(f"Budget Velocity Warning: {budget['category']} budget is {budget['percentage_used']}% consumed with {budget['days_remaining']} days remaining.")

        return {
            "created_alert": created_alert,
            "insights": insights
        }

    # -------------------------------------------------------------------------
    # NODE 7: SYNTHESIZE AND AUDIT
    # -------------------------------------------------------------------------
    def _node_synthesize_and_audit(self, state: AgentState) -> Dict[str, Any]:
        if state.get("requires_clarification"):
            return {
                "final_response": state["final_response"],
                "insights": state.get("insights", [])
            }

        intent = state["intent"]
        results = state["tool_results"]
        entities = state["extracted_entities"]
        insights = list(state.get("insights", []))
        response = ""

        if intent == "add_expense":
            exp = results.get("add_expense", {})
            anom = results.get("detect_anomaly", {})
            budget = results.get("check_budget", {})
            amt = exp.get("amount", entities.get("amount", 0.0))
            merchant = exp.get("merchant", entities.get("merchant", ""))
            category = exp.get("category", "Expense")

            lines = [f"I have recorded your expense of **₹{amt:,.2f}** at **{merchant}** under **{category}**."]

            if anom and anom.get("is_anomaly"):
                lines.append(f"\n⚠️ **Anomaly Alert**: This transaction is significantly higher than your typical spending. {anom.get('reason')}")
            else:
                lines.append(f"\n✓ **Spending Pattern**: Consistent with your normal {category} spending habits.")

            if budget and budget.get("has_budget"):
                lines.append(f"\n📊 **Budget Update**: {category} spending is now at ₹{budget['spent_so_far']:,.2f} of your ₹{budget['monthly_limit']:,.2f} budget ({budget['percentage_used']}% utilized).")
                if budget.get("recommendation"):
                    lines.append(f"💡 *{budget['recommendation']}*")

            response = "\n".join(lines)

        elif intent == "spending_inquiry":
            trend = results.get("calculate_spending_trend", {})
            budget = results.get("check_budget", {})
            cat_spend = results.get("get_category_spending", {})
            cat = cat_spend.get("category", "Food")

            lines = [f"### {cat} Spending Analysis\n"]
            lines.append(f"• **Current Month Total**: ₹{cat_spend.get('total_spending', 0):,.2f} across {cat_spend.get('transaction_count', 0)} transactions.")

            if trend:
                lines.append(f"• **Trend**: {trend.get('explanation')}")

            if budget and budget.get("has_budget"):
                lines.append(f"• **Budget Status**: You have used **{budget.get('percentage_used')}%** of your ₹{budget.get('monthly_limit'):,.2f} budget with {budget.get('days_remaining')} days remaining.")
                lines.append(f"• **Projected Month-End Spend**: ₹{budget.get('projected_spend'):,.2f}.")
                if budget.get("recommendation"):
                    lines.append(f"\n💡 **AI Recommendation**: {budget.get('recommendation')}")
            else:
                lines.append(f"\n💡 **AI Recommendation**: You don't have a budget set for {cat}. Setting a monthly budget of ₹{round(cat_spend.get('total_spending', 5000) * 1.1, -2):,.0f} would help manage this category.")

            response = "\n".join(lines)

        elif intent == "budget_action":
            b_res = results.get("create_budget", {})
            cat = b_res.get("category", "Expense")
            limit = b_res.get("monthly_limit", 5000)
            response = f"✓ I have created a **₹{limit:,.2f}** monthly budget for **{cat}**. I will monitor your velocity and notify you if spending reaches 80% or projects an overrun."

        elif intent == "anomaly_inquiry":
            history = results.get("get_expense_history", [])
            anomalies = [e for e in history if e.get("is_anomaly")]
            if anomalies:
                lines = [f"Found **{len(anomalies)} unusual transactions** in your recent history:\n"]
                for a in anomalies:
                    lines.append(f"• **₹{a['amount']:,.2f}** at **{a['merchant']}** ({a['category']}) on {a['date']} — Anomaly Score: {a.get('anomaly_score')}")
                response = "\n".join(lines)
            else:
                response = "No high-risk anomalous transactions found in your recent history. Your spending conforms to baseline distributions."

        elif intent == "report_inquiry":
            rep = results.get("generate_monthly_report", {})
            response = (
                f"### Monthly Financial Intelligence Report ({rep.get('month_name')})\n\n"
                f"{rep.get('ai_summary')}\n\n"
                f"• **Total Spent**: ₹{rep.get('total_spent', 0):,.2f}\n"
                f"• **Anomalies Flagged**: {rep.get('anomaly_count', 0)}\n\n"
                f"You can view and download the full PDF breakdown in the **Reports** section."
            )

        else:
            monthly = results.get("get_monthly_spending", [])
            latest = monthly[-1] if monthly else {}
            response = (
                f"Hello! I'm FinAgent, your autonomous expense intelligence agent. "
                f"So far this month you have logged ₹{latest.get('total_amount', 0):,.2f} across {latest.get('transaction_count', 0)} transactions. "
                f"How can I assist you with your expenses, budgets, or anomaly analysis today?"
            )

        self._log_event(
            agent_state="Completed",
            decision=f"Generated autonomous agent response for intent: {intent}",
            tool_called="synthesize_response",
            tool_result_summary="Completed full agentic reasoning loop successfully."
        )

        return {
            "final_response": response,
            "insights": insights
        }

    # -------------------------------------------------------------------------
    # AUDIT LOGGING HELPER
    # -------------------------------------------------------------------------
    def _log_event(
        self,
        agent_state: str,
        decision: str,
        tool_called: Optional[str] = None,
        tool_arguments: Optional[Dict[str, Any]] = None,
        tool_result_summary: Optional[str] = None,
        execution_time_ms: int = 0,
        status: str = "success"
    ):
        event = AgentEvent(
            user_id=self.user_id,
            agent_state=agent_state,
            tool_called=tool_called,
            tool_arguments=tool_arguments,
            tool_result_summary=tool_result_summary,
            decision=decision,
            execution_time_ms=execution_time_ms,
            status=status
        )
        self.db.add(event)
        self.db.commit()

    # -------------------------------------------------------------------------
    # MAIN INVOCATION ENTRYPOINT
    # -------------------------------------------------------------------------
    def run(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        initial_state: AgentState = {
            "user_id": self.user_id,
            "input_text": message,
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
        }

        final_state = self.graph.invoke(initial_state)

        return {
            "response": final_state["final_response"],
            "requires_clarification": final_state.get("requires_clarification", False),
            "clarification_prompt": final_state.get("clarification_prompt"),
            "suggested_categories": final_state.get("suggested_categories", []),
            "pending_transaction": final_state.get("extracted_entities") if final_state.get("requires_clarification") else None,
            "tools_executed": final_state.get("executed_tools", []),
            "insights": final_state.get("insights", []),
            "created_expense": final_state.get("created_expense"),
            "created_alert": final_state.get("created_alert")
        }

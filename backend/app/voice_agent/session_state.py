"""
Active Topic State Machine and Working Memory for FinSight Voice Agent.
Maintains conversational state, active topic, active entity, and resolves
elliptical follow-up queries across turns within a session.
"""

import time
import re
import logging
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ActiveTopic(str, Enum):
    CASHFLOW_LIQUIDITY = "cashflow_liquidity"
    SPEND_ANALYSIS = "spend_analysis"
    BUDGETING = "budgeting"
    SAVINGS_GOALS = "savings_goals"
    ANOMALIES = "anomalies"
    BILLS_COMMITMENTS = "bills_commitments"
    CONVERSATIONAL = "conversational"


class WorkingMemoryState(BaseModel):
    user_id: str
    session_id: str
    active_topic: Optional[ActiveTopic] = None
    active_entity: Optional[str] = None
    active_period: Optional[str] = "current_month"
    active_category: Optional[str] = None
    last_tool: Optional[str] = None
    last_tool_data: Optional[Dict[str, Any]] = None
    pending_portal_offer: Optional[Dict[str, Any]] = None
    pending_slack_offer: Optional[Dict[str, Any]] = None
    updated_at: float = Field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def update_state(
        self,
        tool_name: Optional[str] = None,
        category: Optional[str] = None,
        period: Optional[str] = None,
        intent_name: Optional[str] = None,
        tool_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Updates the state machine based on the latest executed turn.
        """
        self.updated_at = time.time()
        if tool_name:
            self.last_tool = tool_name
        if tool_data:
            self.last_tool_data = tool_data
        if period:
            self.active_period = period
        if category:
            self.active_category = category

        # 1. Cashflow & Liquidity Topic
        if tool_name in ("get_spending_summary", "get_forecast", "get_liquidity_buffer") or intent_name in ("cashflow_forecast", "financial_overview", "liquidity_safety_buffer"):
            self.active_topic = ActiveTopic.CASHFLOW_LIQUIDITY
            self.active_entity = "cash_reserve"

        # 2. Spend Analysis Topic
        elif tool_name in ("compare_periods", "get_category_breakdown") or intent_name in ("compare_periods", "category_breakdown"):
            self.active_topic = ActiveTopic.SPEND_ANALYSIS
            self.active_entity = category or "spending_drivers"
            if not category or "food" in str(category).lower() or "dining" in str(category).lower() or tool_name == "compare_periods":
                self.pending_portal_offer = {
                    "tool": "fetch_portal_receipt_forensics",
                    "args": {"merchant": "Swiggy", "order_id": "order-89218"},
                }

        # 3. Anomalies Topic
        elif tool_name == "find_unusual_transactions" or intent_name in ("detect_anomalies", "anomaly_drilldown"):
            self.active_topic = ActiveTopic.ANOMALIES
            self.active_entity = "3_sigma_outliers"
            self.pending_portal_offer = {
                "tool": "fetch_portal_receipt_forensics",
                "args": {"merchant": "Croma", "order_id": "order-49102"},
            }

        # 4. Recurring Bills Topic
        elif tool_name == "get_recurring_payments" or intent_name in ("upcoming_bills", "bill_affordability"):
            self.active_topic = ActiveTopic.BILLS_COMMITMENTS
            self.active_entity = "monthly_commitments"
            self.pending_portal_offer = {
                "tool": "verify_utility_portal_bill",
                "args": {"consumer_id": "102938475"},
            }

        elif tool_name == "fetch_portal_receipt_forensics":
            self.pending_portal_offer = None
            alert_type = "croma_anomaly" if (tool_data and "croma" in str(tool_data).lower()) else "swiggy_surge"
            self.pending_slack_offer = {
                "tool": "dispatch_slack_alert",
                "args": {"alert_type": alert_type, "channel": "#engineering-inventory-tracker"},
            }
        elif tool_name == "verify_utility_portal_bill":
            self.pending_portal_offer = None
            self.pending_slack_offer = {
                "tool": "dispatch_slack_alert",
                "args": {"alert_type": "bescom_bill", "channel": "#engineering-inventory-tracker"},
            }
        elif tool_name == "dispatch_slack_alert":
            self.pending_slack_offer = None

        # 5. Budgeting Topic
        elif tool_name in ("get_budget_plan", "get_budget_status", "prepare_set_budget") or intent_name in ("generate_budget_plan", "set_budget_action"):
            self.active_topic = ActiveTopic.BUDGETING
            self.active_entity = category or "monthly_budget"

        # 6. Savings Goals Topic
        elif tool_name in ("simulate_savings_goal", "simulate_spending_reduction", "prepare_create_goal"):
            self.active_topic = ActiveTopic.SAVINGS_GOALS
            self.active_entity = "vacation_fund"


class WorkingMemoryManager:
    """
    In-memory registry managing WorkingMemoryState instances for active user sessions.
    """
    _sessions: Dict[str, WorkingMemoryState] = {}

    @classmethod
    def get_or_create(cls, user_id: str, session_id: Optional[str] = None) -> WorkingMemoryState:
        key = session_id or f"default_{user_id}"
        if key in cls._sessions:
            return cls._sessions[key]
        # Reuse existing working memory for this user if available
        for existing_key, sess in cls._sessions.items():
            if sess.user_id == user_id:
                cls._sessions[key] = sess
                return sess
        new_state = WorkingMemoryState(
            user_id=user_id,
            session_id=key,
            active_topic=ActiveTopic.CASHFLOW_LIQUIDITY,
            active_entity="cash_reserve",
        )
        cls._sessions[key] = new_state
        return new_state

    @classmethod
    def resolve_elliptical(cls, memory: WorkingMemoryState, query: str) -> Optional[Dict[str, Any]]:
        """
        Resolves elliptical utterances (e.g. 'range kitna hai', 'details do', 'pehle wala', 'क्या बताऊँ')
        against the active topic state machine in English, Hinglish, and Devanagari Hindi.
        """
        lower = query.lower().strip()
        topic = memory.active_topic

        # Pattern 1: Liquidity safety buffer / range inquiry
        # e.g., "range kitna hai", "range kya hai", "kitna range hai", "safe hai kya", "runway kitna hai", "safety buffer"
        if any(w in lower for w in (
            "range kitna hai", "range kya hai", "kitna range", "safe range",
            "safety buffer", "safe hai", "kitna safe", "buffer kitna",
            "runway kitna", "months runway", "safety range", "kitna safe hai",
            "रेंज कितना", "रेंज क्या", "कितना रेंज", "सेफ रेंज", "सुरक्षा बफर",
            "सेफ है", "कितना सेफ", "बफर कितना", "रनवे कितना"
        )):
            if topic in (ActiveTopic.CASHFLOW_LIQUIDITY, ActiveTopic.BILLS_COMMITMENTS) or memory.active_entity == "cash_reserve":
                return {
                    "category": "cashflow_obligations",
                    "confidence": 0.96,
                    "intent_name": "liquidity_safety_buffer",
                    "target_tool": "get_liquidity_buffer",
                    "extracted_args": {"benchmark_months": [3, 6]},
                    "rationale": f"Resolved elliptical range inquiry against active topic '{topic.value if topic else 'cashflow'}' to 3-6 month liquidity buffer benchmark.",
                }

        # Pattern 2: Contextual drill-down on spending drivers
        # e.g., "first one", "pehle wala", "swiggy wala", "second one", "dusra wala"
        if topic == ActiveTopic.SPEND_ANALYSIS:
            if any(w in lower for w in ("first", "pehle", "1st", "number one", "swiggy", "dining", "पहला", "पहला वाला")):
                return {
                    "category": "analytics_explorer",
                    "confidence": 0.95,
                    "intent_name": "category_breakdown",
                    "target_tool": "get_category_breakdown",
                    "extracted_args": {"category": "Food & Dining"},
                    "rationale": "Resolved pronoun 'first one' to Food & Dining driver from active spend analysis topic.",
                }
            if any(w in lower for w in ("second", "dusra", "2nd", "croma", "electronics", "दूसरा", "दूसरा वाला")):
                return {
                    "category": "forensic_anomaly",
                    "confidence": 0.95,
                    "intent_name": "anomaly_drilldown",
                    "target_tool": "find_unusual_transactions",
                    "extracted_args": {"focus": "croma"},
                    "rationale": "Resolved pronoun 'second one' to Croma electronics outlier from active spend analysis topic.",
                }

        # Pattern 3: General "details do", "aur batao", "explain in detail"
        if any(w in lower for w in ("details do", "aur batao", "explain more", "detail me batao", "aur samjhao", "और बताओ", "विस्तार से", "डिटेल्स दो", "और समझाओ")):
            if topic == ActiveTopic.CASHFLOW_LIQUIDITY:
                return {
                    "category": "cashflow_obligations",
                    "confidence": 0.94,
                    "intent_name": "cashflow_forecast",
                    "target_tool": "get_forecast",
                    "extracted_args": {"months_ahead": 3},
                    "rationale": "Resolved 'details do' on cashflow liquidity to 3-month predictive cashflow forecast.",
                }
            if topic == ActiveTopic.ANOMALIES:
                return {
                    "category": "forensic_anomaly",
                    "confidence": 0.94,
                    "intent_name": "anomaly_drilldown",
                    "target_tool": "find_unusual_transactions",
                    "extracted_args": {"lookback_days": 60},
                    "rationale": "Resolved 'details do' on anomalies to full transaction audit logs.",
                }

        # Pattern 4: Contextual Conversational Guidance ("क्या बताऊँ?", "क्या बताऊं", "kya bataun", "aage kya", "what should i ask")
        if any(w in lower for w in (
            "क्या बताऊँ", "क्या बताऊं", "kya bataun", "kya batau", "kya poochun",
            "kya dekhna", "aage kya", "aur kya", "aur kya bata sakte ho", "what can you tell",
            "what next", "where should we start", "what should i ask"
        )):
            if topic in (ActiveTopic.CASHFLOW_LIQUIDITY, ActiveTopic.BILLS_COMMITMENTS):
                return {
                    "category": "cashflow_obligations",
                    "confidence": 0.95,
                    "intent_name": "conversational_guidance",
                    "target_tool": "get_liquidity_buffer",
                    "extracted_args": {"benchmark_months": [3, 6]},
                    "rationale": "User inquired what to explore next following liquidity safety buffer analysis.",
                }
            elif topic == ActiveTopic.SPEND_ANALYSIS:
                return {
                    "category": "analytics_explorer",
                    "confidence": 0.95,
                    "intent_name": "conversational_guidance",
                    "target_tool": "get_category_breakdown",
                    "extracted_args": {},
                    "rationale": "User inquired what to explore next following spending analysis.",
                }

        # Pattern 5: Brief status inquiry / STT garble ("चाक्या है मेरा", "क्या है मेरा", "मेरा क्या है")
        if any(w in lower for w in ("चाक्या है मेरा", "क्या है मेरा", "मेरा क्या है", "kya hai mera", "mera kya hai", "balance kya hai", "status kya hai")):
            if topic in (ActiveTopic.CASHFLOW_LIQUIDITY, ActiveTopic.BILLS_COMMITMENTS) or memory.active_entity == "cash_reserve":
                return {
                    "category": "cashflow_obligations",
                    "confidence": 0.94,
                    "intent_name": "liquidity_safety_buffer",
                    "target_tool": "get_liquidity_buffer",
                    "extracted_args": {"benchmark_months": [3, 6]},
                    "rationale": "Resolved balance inquiry / STT artifact against active cashflow context.",
                }
            elif topic == ActiveTopic.SPEND_ANALYSIS:
                return {
                    "category": "analytics_explorer",
                    "confidence": 0.94,
                    "intent_name": "category_breakdown",
                    "target_tool": "get_category_breakdown",
                    "extracted_args": {"period": memory.active_period or "current_month"},
                    "rationale": "Resolved status inquiry / STT artifact against active spend analysis context.",
                }
            else:
                return {
                    "category": "analytics_explorer",
                    "confidence": 0.90,
                    "intent_name": "financial_overview",
                    "target_tool": "get_spending_summary",
                    "extracted_args": {"period": "current_month"},
                    "rationale": "Resolved status inquiry to overall financial overview.",
                }

        return None

"""
Hierarchical Intent Classifier and Domain Router for FinSight.
Accurately categorizes user queries, isolates conversational/meta inquiries
to minimize LLM token usage and prevent unwanted financial calculations,
and routes domain queries to specialized financial agents.
"""

import re
import logging
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.app.voice_agent.session_state import WorkingMemoryManager, WorkingMemoryState, ActiveTopic
from backend.app.voice_agent.semantic_classifier import FastSemanticClassifier
from backend.app.voice_agent.bm25_tool_retriever import bm25_retriever

logger = logging.getLogger(__name__)


class IntentCategory(str, Enum):
    GREETING_AND_META = "greeting_and_meta"
    FORENSIC_ANOMALY = "forensic_anomaly"
    PREDICTIVE_ADVISORY = "predictive_advisory"
    ANALYTICS_EXPLORER = "analytics_explorer"
    CASHFLOW_OBLIGATIONS = "cashflow_obligations"
    OPERATIONAL_ACTION = "operational_action"
    PORTAL_AUTOMATION = "portal_automation"


class IntentClassificationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: IntentCategory
    confidence: float = Field(ge=0.0, le=1.0)
    intent_name: str = Field(min_length=1, max_length=100)
    target_tool: Optional[str] = Field(default=None, max_length=100)
    secondary_tool: Optional[str] = Field(default=None, max_length=100)
    extracted_args: Dict[str, Any] = Field(default_factory=dict)
    rationale: str = Field(default="", max_length=500)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "confidence": self.confidence,
            "intent_name": self.intent_name,
            "target_tool": self.target_tool,
            "secondary_tool": self.secondary_tool,
            "extracted_args": self.extracted_args,
            "rationale": self.rationale,
        }


class IntentRouter:
    """
    High-precision, multi-tiered intent classifier.
    Tier 1: Conversational / Meta / Greeting Filter (Bypasses heavy SQL / saves tokens)
    Tier 2: Action Operator Intent Filter (Budget capping, goal creation)
    Tier 3: Domain Semantic Pattern Matcher (Anomalies, Forecasts, Breakdown, Bills)
    Tier 4: Conversational Context & Pronoun Resolution
    """

    # 1. Greetings & Meta Expressions (Exact & Pattern)
    AUDIO_CHECK_PATTERNS = [
        r"\b(?:can\s+you\s+hear(?:\s+to)?\s+me|can\s+you\s+hear\b|hear\s+to\s+me|hear\s+me|am\s+i\s+audible|are\s+you\s+hearing\b|are\s+you\s+listening|can\s+you\s+listen(?:\s+to\s+me)?|listen\s+to\s+me|sun\s+rahe\s+ho|sunai\s+de\s+raha\s+hai|awaaz\s+aa\s+rahi\s+hai|mic\s+check|sound\s+check|audio\s+test|testing\s+mic)\b",
        r"(?:सुन\s+रहे\s+हो|आवाज़\s+आ\s+रही\s+है|आवाज\s+आ\s+रही\s+है|माइक\s+चेक|ऑडियो\s+टेस्ट|सुनाई\s+दे\s+रहा\s+है)",
    ]

    GREETING_PATTERNS = [
        r"^(?:hi|hello|hey|namaste|namaskar|pranam|hola|good\s+(?:morning|afternoon|evening|day)|howdy)\b",
        r"\b(?:hey\s+finch|hi\s+finch|hello\s+finch|finch|hey\s+finsight|hi\s+finsight|hello\s+finsight|finsight)\b",
        r"^(?:नमस्ते|नमस्कार|प्रणाम|हाय|हैलो)\b",
        r"\b(?:just\s+greeting|only\s+greeting|saying\s+hi|saying\s+hello)\b",
        r"\b(?:how\s+are\s+you|how's\s+it\s+going|how\s+do\s+you\s+do|how\s+are\s+you\s+doing|how're\s+you\s+doing|what's\s+up|kaise\s+ho|kya\s+haal\s+hai|कैसे\s+हो|क्या\s+हाल\s+है)\b",
        r"\b(?:who\s+are\s+you|what\s+is\s+your\s+name|introduce\s+yourself|aap\s+kaun\s+ho|tum\s+kaun\s+ho|आप\s+कौन\s+हो|तुम\s+कौन\s+हो)\b",
        r"\b(?:what\s+can\s+you\s+do|how\s+can\s+you\s+help|what\s+are\s+your\s+skills|kya\s+kar\s+sakte\s+ho|क्या\s+कर\s+सकते\s+हो|क्या\s+मदद\s+कर\s+सकते\s+हो)\b",
        r"\b(?:thank\s+you|thanks|thx|cheers|appreciate\s+it|shukriya|dhanyawad|शुक्रिया|धन्यवाद)\b",
        r"\b(?:bye|goodbye|see\s+you|talk\s+later|alvida|अलविदा)\b",
        r"^(?:ok|okay|got\s+it|understood|alright|cool|theek\s+hai|accha|sounds\s+good|perfect|great|done|ठीक\s+है|अच्छा)[.!]?\s*$",
    ]

    META_FEEDBACK_PATTERNS = [
        r"\b(?:why\s+are\s+you\s+giving\s+me\s+these\s+answers|why\s+are\s+you\s+answering\s+like\s+this)\b",
        r"\b(?:why\s+did\s+you\s+say\s+that|i\s+didn't\s+ask\s+that|that's\s+not\s+what\s+i\s+asked)\b",
        r"\b(?:stop\s+talking|be\s+quiet|shut\s+up|pause|hold\s+on|wait\s+a\s+sec|chup\s+raho|shant\s+raho|चुप\s+रहो|शांत\s+रहो)\b",
        r"\b(?:listen\s+to\s+me|just\s+listen|मेरी\s+बात\s+सुनो)\b",
        r"\b(?:i\s+am\s+just\s+talking|just\s+testing|just\s+chatting|main\s+bas\s+baat\s+kar\s+raha\s+hoon|सिर्फ\s+बात\s+कर\s+रहा\s+हूँ)\b",
    ]

    @classmethod
    def classify(
        cls,
        query: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        working_memory: Optional[WorkingMemoryState] = None,
    ) -> IntentClassificationResult:
        res = cls._classify_core(query, conversation_history, working_memory)
        if res.category != IntentCategory.GREETING_AND_META:
            p_tool, s_tool = bm25_retriever.detect_multi_intent(query)
            if p_tool and s_tool:
                if res.target_tool == s_tool:
                    res.target_tool = p_tool
                    res.secondary_tool = s_tool
                elif res.target_tool == p_tool:
                    res.secondary_tool = s_tool
                else:
                    res.secondary_tool = s_tool
                res.rationale += f" [Multi-intent detected: primary={res.target_tool}, secondary={res.secondary_tool}]"
        return res

    @classmethod
    def _classify_core(
        cls,
        query: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        working_memory: Optional[WorkingMemoryState] = None,
    ) -> IntentClassificationResult:
        raw_text = query.strip()
        lower = raw_text.lower()
        clean_text = re.sub(r"[^\w\s₹,.]", " ", lower).strip()
        has_history = conversation_history is not None and len(conversation_history) > 0
        last_turn = conversation_history[-1] if has_history else {}
        last_tool = last_turn.get("tool_name", "")

        # -----------------------------------------------------------------
        # TIER 1: Greeting & Conversational Meta (High Priority Token Saver)
        # -----------------------------------------------------------------
        # Check audio check / microphone connectivity first
        for pat in cls.AUDIO_CHECK_PATTERNS:
            if re.search(pat, lower):
                return IntentClassificationResult(
                    category=IntentCategory.GREETING_AND_META,
                    confidence=0.99,
                    intent_name="audio_check",
                    target_tool=None,
                    rationale="User is checking microphone, audio reception, or voice connectivity.",
                )

        # Check meta feedback: "I am talking I'm just greeting you why are you giving me these answers"
        for pat in cls.META_FEEDBACK_PATTERNS:
            if re.search(pat, lower):
                return IntentClassificationResult(
                    category=IntentCategory.GREETING_AND_META,
                    confidence=0.99,
                    intent_name="conversational_clarification",
                    target_tool=None,
                    rationale="User is providing conversational feedback or asking why the agent answered in a certain way without asking for financial metrics.",
                )

        # Check pure greetings and pleasantries
        for pat in cls.GREETING_PATTERNS:
            if re.search(pat, lower):
                # Ensure it's not a compound financial query like "Hello, what is my balance?"
                has_financial_intent = any(
                    w in lower for w in ("balance", "spend", "bought", "budget", "bill", "anomaly", "invest", "forecast", "transaction", "खर्च", "बैलेंस")
                )
                if not has_financial_intent:
                    is_ack = bool(re.search(r"^(?:ok|okay|got\s+it|understood|alright|cool|theek\s+hai|accha|sounds\s+good|perfect|great|done|ठीक\s+है|अच्छा)[.!]?\s*$", lower))
                    return IntentClassificationResult(
                        category=IntentCategory.GREETING_AND_META,
                        confidence=0.98,
                        intent_name="acknowledgment" if is_ack else "greeting",
                        target_tool=None,
                        rationale="User query is a pure conversational greeting or acknowledgment. No heavy SQL or DOM scraping calculations required.",
                    )

        # -----------------------------------------------------------------
        # TIER 2: Operational Action Intents (Budget Capping & Goals)
        # -----------------------------------------------------------------
        if any(w in lower for w in (
            "set budget", "set my", "budget to", "cap food", "cap my", "set a budget", "limit food",
            "budget set", "budget fix", "set kardo", "fix kardo", "budget bana do", "बजट सेट", "बजट बना"
        )):
            m = re.search(r'(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?)', lower)
            amt = 15000.0
            if m:
                clean_num = m.group(1).replace(",", "")
                try:
                    val = float(clean_num)
                    if val > 0:
                        amt = val
                except ValueError:
                    pass
            cat = "Food & Dining" if ("food" in lower or "dining" in lower) else ("Shopping" if "shopping" in lower else "Discretionary")
            return IntentClassificationResult(
                category=IntentCategory.OPERATIONAL_ACTION,
                confidence=0.95,
                intent_name="set_budget_action",
                target_tool="prepare_set_budget",
                extracted_args={"category": cat, "amount": amt},
                rationale=f"User is requesting to set a monthly budget for {cat} at ₹{amt:,.0f}.",
            )

        if any(w in lower for w in (
            "create a savings", "create savings", "create a vacation", "new savings goal", "create goal",
            "goal bana do", "goal create", "goal set kardo", "नया गोल", "गोल बना"
        )):
            target = 60000.0
            if "50" in lower or "50000" in lower:
                target = 50000.0
            elif "100000" in lower or "1 lakh" in lower or "1,00,000" in lower:
                target = 100000.0
            name = "Vacation Fund" if ("vacation" in lower or "trip" in lower) else "Emergency Fund"
            return IntentClassificationResult(
                category=IntentCategory.OPERATIONAL_ACTION,
                confidence=0.95,
                intent_name="create_goal_action",
                target_tool="prepare_create_goal",
                extracted_args={"name": name, "target_amount": target, "target_date": "2027-06-30"},
                rationale=f"User is requesting to create a {name} savings goal with target ₹{target:,.0f}.",
            )

        # Conversational Confirmation of Pending Slack Alert Offer
        if working_memory and getattr(working_memory, "pending_slack_offer", None):
            is_slack_affirmative = any(
                w in lower
                for w in (
                    "yes", "yeah", "sure", "send it", "send alert", "send slack", "bhej do",
                    "bhejo", "haan", "ha", "bhejna", "alert bhejo", "kar do", "post it", "notify slack",
                    "हाँ", "हां", "भेजो", "भेज दो", "अलर्ट भेजो", "कर दो", "स्लैक पर भेजो",
                    "send", "bhej"
                )
            ) and not any(w in lower for w in ("balance", "kitna bacha", "kiraya", "groceries", "rent", "kya bataun", "kya batao", "receipt"))
            if is_slack_affirmative:
                offer = working_memory.pending_slack_offer
                return IntentClassificationResult(
                    category=IntentCategory.OPERATIONAL_ACTION,
                    confidence=0.98,
                    intent_name="dispatch_slack_alert",
                    target_tool=offer.get("tool", "dispatch_slack_alert"),
                    extracted_args=offer.get("args", {"alert_type": "swiggy_surge", "channel": "#engineering-inventory-tracker"}),
                    rationale="User confirmed autonomous Slack alert dispatch offer from active conversational working memory.",
                )

        # Slack Notification and Autonomous Trigger Dispatch (Dynamic & Generalized)
        if any(w in lower for w in (
            "slack", "slack pe", "slack me", "slack par", "slack alert",
            "send to slack", "post on slack", "slack notification", "slack par bhej do",
            "slack pe bhejo", "slack alert set", "slack alert chahiye", "slack connect",
            "give me a slack alert", "give me slack alert", "slack alert for", "send a slack alert",
            "स्लैक", "स्लैक अलर्ट", "स्लैक पर भेजो", "स्लैक नोटिफिकेशन", "स्लैक पर अलर्ट"
        )):
            # 1. Extract optional target category
            detected_category = None
            cat_map = {
                "food & dining": "Food & Dining",
                "food": "Food & Dining",
                "dining": "Food & Dining",
                "khana": "Food & Dining",
                "shopping": "Shopping",
                "kharidari": "Shopping",
                "खरीदारी": "Shopping",
                "groceries": "Groceries",
                "grocery": "Groceries",
                "kirana": "Groceries",
                "राशन": "Groceries",
                "electronics": "Electronics",
                "transportation": "Transportation",
                "travel": "Transportation",
                "transport": "Transportation",
                "cab": "Transportation",
                "utilities": "Utilities",
                "electricity": "Utilities",
                "bijli": "Utilities",
                "बिजली": "Utilities",
                "entertainment": "Entertainment",
                "healthcare": "Healthcare",
            }
            for kw, cat_name in cat_map.items():
                if kw in lower:
                    detected_category = cat_name
                    break

            # 2. Extract optional numerical threshold (e.g., "above 5000", "₹10,000")
            threshold_val = None
            num_match = re.search(r'(?:above|exceeding|greater than|over|more than|≥|>|se zyada|से ज्यादा|₹|rs\.?|inr)\s*(\d+(?:,\d+)*)', lower)
            if num_match:
                try:
                    threshold_val = float(num_match.group(1).replace(",", ""))
                except Exception:
                    threshold_val = None

            # 3. Detect specific Alert Type
            alert_type = "test"
            if any(w in lower for w in ("breach", "limit", "budget", "ceiling", "exceed", "खत्म", "बजट")):
                alert_type = "budget_breach"
            elif any(w in lower for w in ("surge", "spike", "upsurge", "increase", "jump", "delta", "उछाल", "बढ़", "बढ़ोतरी")):
                alert_type = "spending_spike"
            elif any(w in lower for w in ("anomaly", "fraud", "unusual", "suspicious", "outlier", "gadbad", "गड़बड़")):
                alert_type = "croma_anomaly"
            elif any(w in lower for w in ("bill", "bescom", "electricity", "broadband", "fibernet", "due", "बिल")):
                alert_type = "bescom_bill"
            elif any(w in lower for w in ("goal", "vacation", "target", "milestone", "लक्ष्य")):
                alert_type = "goal_velocity"
            elif threshold_val or any(w in lower for w in ("high value", "large", "big transaction", "bada kharcha", "बड़ा खर्च")):
                alert_type = "high_transaction"
            elif any(w in lower for w in ("swiggy", "receipt", "zomato", "delivery", "स्विगी", "रसीद")):
                alert_type = "swiggy_surge"
            elif detected_category:
                alert_type = "category_alert"
            elif working_memory and working_memory.last_tool:
                if "budget" in working_memory.last_tool:
                    alert_type = "budget_breach"
                elif "compare" in working_memory.last_tool:
                    alert_type = "spending_spike"
                elif "portal_receipt" in working_memory.last_tool:
                    alert_type = "swiggy_surge"
                elif "bill" in working_memory.last_tool or "recurring" in working_memory.last_tool:
                    alert_type = "bescom_bill"
                elif "unusual" in working_memory.last_tool:
                    alert_type = "croma_anomaly"
                elif "category" in working_memory.last_tool:
                    alert_type = "category_alert"
                else:
                    alert_type = "custom_dynamic"
            elif any(w in lower for w in ("runway", "cashflow", "balance", "reserve", "savings", "income")):
                alert_type = "custom_dynamic"

            extracted_args = {
                "alert_type": alert_type,
                "channel": "#engineering-inventory-tracker",
                "custom_topic": detected_category or working_memory.active_category if working_memory else detected_category,
                "threshold_amount": threshold_val or 5000.0,
            }

            return IntentClassificationResult(
                category=IntentCategory.OPERATIONAL_ACTION,
                confidence=0.98,
                intent_name="dispatch_slack_alert",
                target_tool="dispatch_slack_alert",
                extracted_args=extracted_args,
                rationale=f"User requested autonomous Slack financial notification dispatch for {alert_type} (topic: {extracted_args.get('custom_topic')}).",
            )

        # -----------------------------------------------------------------
        # TIER 2.5: Browser Portal Automation & Forensic Receipts
        # (Triggered ONLY for explicit receipt requests or confirmed offers)
        # -----------------------------------------------------------------
        if working_memory and working_memory.pending_portal_offer:
            is_affirmative = any(
                w in lower
                for w in (
                    "yes", "yeah", "sure", "show me", "open it", "open receipt", "verify it",
                    "check it", "haan", "ha", "dikhao", "batao", "karo", "check karo",
                    "khol ke dikhao", "receipt dikhao", "bill dikhao", "verify karo", "portal kholo",
                    "open karo", "dikhao", "kholo",
                    # Devanagari Hindi variants
                    "हाँ", "हां", "दिखाओ", "दिखाइए", "दिखा", "खोलो", "खोल", "ओपन", "ओपन करो",
                    "करो", "चेक करो", "चेक", "खोल के दिखाओ", "दिखा दो", "अच्छा दिखाओ", "बिल दिखाओ",
                    "रसीद दिखाओ", "रसीद", "पोर्टल खोलो", "खोल दिया", "खोल दो"
                )
            ) or ("receipt" in lower and any(w in lower for w in ("open", "show", "view", "khol", "kholo", "dikhao", "खोलो", "दिखाओ", "करो", "ओपन")))
            if is_affirmative and not any(w in lower for w in ("balance", "kitna bacha", "kiraya", "groceries", "rent", "kya bataun", "kya batao")):
                offer = working_memory.pending_portal_offer
                return IntentClassificationResult(
                    category=IntentCategory.PORTAL_AUTOMATION,
                    confidence=0.98,
                    intent_name="portal_evidence_drilldown",
                    target_tool=offer.get("tool", "fetch_portal_receipt_forensics"),
                    extracted_args=offer.get("args", {}),
                    rationale="User confirmed visual portal drilldown offer from active conversational working memory.",
                )

        has_receipt_intent = (
            ("receipt" in lower or "रसीद" in lower or "invoice" in lower or "swiggy" in lower or "स्विगी" in lower)
            and any(w in lower for w in ("open", "show", "view", "khol", "kholo", "dikhao", "खोलो", "दिखाओ", "करो", "ओपन", "details", "bill", "बिल"))
        ) or any(w in lower for w in ("open receipt", "show receipt", "receipt kholo", "receipt dikhao", "receipt open"))
        if has_receipt_intent and not any(w in lower for w in ("balance", "kitna bacha", "kiraya", "groceries", "rent")):
            merchant = "Swiggy"
            order_id = "order-89218"
            if "croma" in lower or "क्रोमा" in lower or "cable" in lower:
                merchant = "Croma"
                order_id = "order-49102"
            return IntentClassificationResult(
                category=IntentCategory.PORTAL_AUTOMATION,
                confidence=0.98,
                intent_name="portal_swiggy_receipt",
                target_tool="fetch_portal_receipt_forensics",
                extracted_args={"merchant": merchant, "order_id": order_id},
                rationale=f"User explicitly requested {merchant} itemized receipt forensics.",
            )

        if ("bescom" in lower and any(w in lower for w in ("portal", "verify", "bill", "reading", "meter", "online", "check"))) or any(w in lower for w in ("bescom portal", "portal pe verify", "verify on portal", "bijli ka bill portal", "bescom bill verify", "verify electricity bill", "check meter reading", "verify bill on portal", "बिजली बिल")):
            return IntentClassificationResult(
                category=IntentCategory.PORTAL_AUTOMATION,
                confidence=0.98,
                intent_name="portal_bescom_verification",
                target_tool="verify_utility_portal_bill",
                extracted_args={"consumer_id": "102938475"},
                rationale="User explicitly requested Bescom utility portal verification.",
            )

        if ("croma" in lower and any(w in lower for w in ("receipt", "invoice", "bill", "order", "proof", "cable", "purchase", "item"))) or any(w in lower for w in ("croma receipt", "croma invoice", "receipt for croma", "croma ka bill", "croma purchase proof")):
            return IntentClassificationResult(
                category=IntentCategory.PORTAL_AUTOMATION,
                confidence=0.98,
                intent_name="portal_croma_receipt",
                target_tool="fetch_portal_receipt_forensics",
                extracted_args={"merchant": "Croma", "order_id": "order-49102"},
                rationale="User explicitly requested Croma hardware invoice verification.",
            )

        # -----------------------------------------------------------------
        # TIER 3: Contextual Pronoun & Elliptical Resolution via Working Memory
        # -----------------------------------------------------------------
        # Check active topic state machine first
        if working_memory is not None:
            resolved = WorkingMemoryManager.resolve_elliptical(working_memory, query)
            if resolved:
                return IntentClassificationResult(
                    category=IntentCategory(resolved["category"]),
                    confidence=resolved["confidence"],
                    intent_name=resolved["intent_name"],
                    target_tool=resolved.get("target_tool"),
                    extracted_args=resolved.get("extracted_args", {}),
                    rationale=resolved["rationale"],
                )

        if has_history and any(w in lower for w in ("first", "second", "that", "more", "explain", "detail", "tell me more")):
            # If prior turn was spending increase comparison
            if last_tool == "compare_periods":
                if any(w in lower for w in ("first", "food", "dining", "swiggy", "zomato")):
                    return IntentClassificationResult(
                        category=IntentCategory.ANALYTICS_EXPLORER,
                        confidence=0.92,
                        intent_name="category_drilldown",
                        target_tool="get_category_breakdown",
                        extracted_args={"category": "Food & Dining"},
                        rationale="Resolving pronoun 'the first one' to Food & Dining driver from prior comparison.",
                    )
                if any(w in lower for w in ("second", "croma", "electronic", "shopping", "other")):
                    return IntentClassificationResult(
                        category=IntentCategory.FORENSIC_ANOMALY,
                        confidence=0.92,
                        intent_name="anomaly_drilldown",
                        target_tool="find_unusual_transactions",
                        extracted_args={"focus": "croma"},
                        rationale="Resolving pronoun 'the second one' to Croma electronics outlier.",
                    )

            if last_tool in ("get_recurring_payments", "find_unusual_transactions"):
                if any(w in lower for w in ("afford", "enough", "balance", "safe", "cover")):
                    return IntentClassificationResult(
                        category=IntentCategory.CASHFLOW_OBLIGATIONS,
                        confidence=0.94,
                        intent_name="bill_affordability",
                        target_tool="get_recurring_payments",
                        extracted_args={"days_ahead": 30},
                        rationale="Checking liquid cash reserve coverage against upcoming obligations.",
                    )

        # -----------------------------------------------------------------
        # TIER 4: Domain Specific Intent Classification
        # -----------------------------------------------------------------
        # 4A_0. Category Budget Alert Disambiguation (e.g. "Dining alert.", "food alert", "set alert", "budget alert")
        # Disambiguates category alerts away from 3-sigma forensic anomaly scans!
        is_category_alert = ("alert" in lower or "limit" in lower or "threshold" in lower or "अलर्ट" in lower) and any(
            c in lower for c in ("dining", "food", "shopping", "groceries", "transport", "budget", "cap", "monthly", "spend", "खाना", "शॉपिंग", "बजट")
        )
        if is_category_alert:
            cat = "Food & Dining" if any(c in lower for c in ("food", "dining", "खाना")) else ("Shopping" if ("shopping" in lower or "शॉपिंग" in lower) else None)
            return IntentClassificationResult(
                category=IntentCategory.ANALYTICS_EXPLORER,
                confidence=0.96,
                intent_name="budget_status",
                target_tool="get_budget_status",
                extracted_args={"category": cat} if cat else {},
                rationale=f"User requested category budget alert and threshold status for {cat or 'configured budgets'}.",
            )

        # 4A. Forensic & Anomalies
        if (any(w in lower for w in ("anomal", "unusual", "irregular", "fraud", "suspicio", "flag", "weird", "strange", "outlier", "gadbad", "galat", "anokha", "sandigdh", "गड़बड़", "गलत", "असामान्य", "संदिग्ध", "धोखाधड़ी", "फ्रॉड", "अनियमित")) or
            ("alert" in lower and not is_category_alert and any(w in lower for w in ("fraud", "unusual", "suspicio", "security", "transaction", "anomal", "लेनदेन")))):
            return IntentClassificationResult(
                category=IntentCategory.FORENSIC_ANOMALY,
                confidence=0.96,
                intent_name="detect_anomalies",
                target_tool="find_unusual_transactions",
                extracted_args={"lookback_days": 60},
                rationale="Checking recent transactions against configured review rules.",
            )

        # 4B. Predictive Advisory: Prescriptive Budget Planning & Spending Optimization Strategy
        # Evaluated BEFORE descriptive historical breakdown to correctly prioritize compound questions
        # like "अच्छा, मेरे को ये बताओ कि मेरे को कितना खर्चा करना चाहिए और कहाँ पे कम करना चाहिए?"
        has_prescriptive_advisory = any(
            w in lower for w in (
                "कम करना चाहिए", "कहाँ कम", "कहाँ पे कम", "कितना खर्चा करना चाहिए", "कितना खर्च करना चाहिए",
                "खर्च कम", "खर्चा कम", "बचत कैसे", "बचाना चाहिए", "कहाँ कटौती", "सुझाव", "सलाह",
                "how much should i spend", "where should i cut", "where to cut", "cut down",
                "how much to spend", "where can i save", "where to reduce", "how much can i spend",
                "budget plan", "plan my budget", "plan next month", "recommend a budget", "plan for me",
                "plan for next month", "prepare a next month", "prepare budget", "budget banao", "plan banao",
                "बजट बनाओ", "प्लान बनाओ", "योजना बनाओ", "नया बजट", "बजट प्लान", "अगले महीने का बजट"
            )
        )
        if has_prescriptive_advisory:
            return IntentClassificationResult(
                category=IntentCategory.PREDICTIVE_ADVISORY,
                confidence=0.97,
                intent_name="generate_budget_plan",
                target_tool="get_budget_plan",
                extracted_args={},
                rationale="Formulating prescriptive income-constrained budget plan and spending reduction strategy.",
            )

        # 4C. Predictive Advisory: What-If Discretionary Simulation
        if any(w in lower for w in ("what if", "what-if", "reduce dining", "cut dining", "if i reduce", "if i cut", "how much will i save", "save if i cut", "save if i reduce", "कम करें", "बचत होगी", "कटौती")):
            m = re.search(r'(\d+(?:\.\d+)?)\s*(?:%|percent)', lower)
            pct = float(m.group(1)) if m else 20.0
            cat = "Food & Dining" if ("food" in lower or "dining" in lower or "खाना" in lower) else "Shopping"
            return IntentClassificationResult(
                category=IntentCategory.PREDICTIVE_ADVISORY,
                confidence=0.95,
                intent_name="simulate_reduction",
                target_tool="simulate_spending_reduction",
                extracted_args={"category": cat, "reduction_pct": pct, "goal_name": "Vacation Fund" if "vacation" in lower else None},
                rationale=f"Simulating {pct:.0f}% discretionary cut on {cat}.",
            )

        # 4D. Predictive Advisory: Savings Goal Milestone
        if any(w in lower for w in ("vacation fund", "goal progress", "reach my goal", "savings goal", "simulate goal")):
            return IntentClassificationResult(
                category=IntentCategory.PREDICTIVE_ADVISORY,
                confidence=0.93,
                intent_name="simulate_goal",
                target_tool="simulate_savings_goal",
                extracted_args={
                    "goal_name": "Vacation Fund" if "vacation fund" in lower else None,
                    "discretionary_reduction_pct": 20.0,
                },
                rationale="Computing savings milestone acceleration timeline.",
            )

        # 4E. Cashflow & Obligations: Future Cashflow Forecast
        if any(w in lower for w in ("forecast", "predict", "project", "future", "trajectory", "cashflow", "भविष्य", "पूर्वानुमान", "आगे का खर्च", "अनुमान")):
            return IntentClassificationResult(
                category=IntentCategory.CASHFLOW_OBLIGATIONS,
                confidence=0.95,
                intent_name="cashflow_forecast",
                target_tool="get_forecast",
                extracted_args={"months_ahead": 3},
                rationale="Holt-Winters double exponential smoothing forecast.",
            )

        # 4F_1. Cashflow & Obligations: Liquidity Safety Buffer / Runway Range (Checked before bills)
        if any(w in lower for w in (
            "range", "buffer", "safe range", "safety buffer", "safe hai", "kitna safe", "buffer kitna",
            "runway", "safety range", "cushion", "reserve",
            "रेंज", "बफर", "सेफ रेंज", "सुरक्षा बफर", "कितना सेफ", "सेफ है", "रनवे", "सुरक्षा दायरा", "सुरक्षित", "रिजर्व"
        )):
            return IntentClassificationResult(
                category=IntentCategory.CASHFLOW_OBLIGATIONS,
                confidence=0.96,
                intent_name="liquidity_safety_buffer",
                target_tool="get_liquidity_buffer",
                extracted_args={"benchmark_months": [3, 6]},
                rationale="User requested verified liquidity safety buffer and 3-6 month emergency reserve benchmarks.",
            )

        # 4F_2. Cashflow & Obligations: Recurring Payments & Bills
        if any(w in lower for w in ("bill", "recurring", "subscription", "autopay", "netflix", "due", "rent", "kiraya", "bijli", "bescom", "airtel", "bills bhar", "बिल", "किस्त", "सब्सक्रिप्शन", "देय", "भुगतान", "किराया", "बिजली")):
            return IntentClassificationResult(
                category=IntentCategory.CASHFLOW_OBLIGATIONS,
                confidence=0.94,
                intent_name="upcoming_bills",
                target_tool="get_recurring_payments",
                extracted_args={"days_ahead": 30},
                rationale="Fetching upcoming commitments and balance buffer.",
            )

        # 4G. Analytics Explorer: Financial Spend Increase / Variance
        # NOTE: Must include financial context ('spend', 'money', 'cost', 'expense', or digits like '8000')
        # to prevent catching conversational 'why' queries!
        has_financial_context = any(
            w in lower for w in ("spend", "spent", "money", "cost", "expense", "8000", "8,000", "rupee", "rs", "inr", "surge", "spike", "kharch", "kharcha", "kharche", "paisa", "paise", "खर्च", "खर्चा", "खर्चे", "पैसे", "पैसा", "रुपये")
        )
        if has_financial_context and any(w in lower for w in ("increase", "spike", "more", "why did", "why has", "compare", "growth", "rose", "badha", "badh", "kyu", "kyun", "बढ़ा", "बढ़", "ज्यादा", "अधिक", "क्यों", "तुलना")):
            return IntentClassificationResult(
                category=IntentCategory.ANALYTICS_EXPLORER,
                confidence=0.94,
                intent_name="compare_periods",
                target_tool="compare_periods",
                extracted_args={"period_1": "current_month", "period_2": "previous_month"},
                rationale="Comparing monthly expense periods to identify spending spike drivers.",
            )

        # 4H. Analytics Explorer: Category Spending Breakdown
        has_breakdown_keyword = any(w in lower for w in ("breakdown", "category", "categories", "distribution", "kahan gaya", "kahan hua", "व्यय", "ब्यौरा", "वितरण", "खाता"))
        has_spending_keyword = any(w in lower for w in ("spend", "spent", "expense", "expenses", "kharch", "kharcha", "kharche", "खर्च", "खर्चा", "खर्चे"))
        has_category_name = any(w in lower for w in ("food", "dining", "shopping", "transport", "travel", "groceries", "खाना", "शॉपिंग", "यात्रा", "किराना"))
        is_category_inquiry = has_breakdown_keyword or has_category_name or (has_spending_keyword and any(w in lower for w in ("where", "kahan", "kitna", "how much", "tell", "show", "कहाँ", "कितना", "बताओ", "दिखाओ", "बताइए", "दिखाइए", "pichle", "पिछले", "पिछला")))

        if is_category_inquiry:
            target_cat = None
            if "food" in lower or "dining" in lower or "खाना" in lower:
                target_cat = "Food & Dining"
            elif "shopping" in lower or "शॉपिंग" in lower:
                target_cat = "Shopping"
            elif "transport" in lower or "travel" in lower or "यात्रा" in lower:
                target_cat = "Transportation"

            # Check if previous month is explicitly mentioned
            period = "current_month"
            if any(w in lower for w in ("last month", "previous month", "pichle mahine", "pichla mahina", "पिछले महीने", "पिछला महीना", "गत माह", "पूर्व माह")):
                period = "previous_month"

            return IntentClassificationResult(
                category=IntentCategory.ANALYTICS_EXPLORER,
                confidence=0.95,
                intent_name="category_breakdown",
                target_tool="get_category_breakdown",
                extracted_args={"category": target_cat, "period": period} if target_cat else {"period": period},
                rationale=f"Aggregating category spending breakdown{f' for {target_cat}' if target_cat else ''} ({period}).",
            )

        # 4I. Analytics Explorer: Payment Modes & Top Merchants
        if any(w in lower for w in ("upi", "merchant", "counterparty", "swiggy", "uber", "mode", "payment")):
            return IntentClassificationResult(
                category=IntentCategory.ANALYTICS_EXPLORER,
                confidence=0.91,
                intent_name="payment_merchants",
                target_tool="get_payment_mode_summary",
                extracted_args={"mode": "UPI", "limit": 5},
                rationale="Aggregating counterparty merchant volume for payment modes.",
            )

        # 4J. Active Budget Status & Limits
        if any(w in lower for w in ("budget", "cap", "limit", "control", "utilization")):
            return IntentClassificationResult(
                category=IntentCategory.ANALYTICS_EXPLORER,
                confidence=0.91,
                intent_name="budget_status",
                target_tool="get_budget_status",
                extracted_args={},
                rationale="Evaluating active category budget thresholds and utilization.",
            )


        # 4L. Relative Time Period Shorthand Queries (e.g. "last month.", "previous month", "this month", "पिछले महीने का खर्चा")
        if re.search(r"\b(?:last\s+month|previous\s+month|pichle\s+mahine|pichla\s+mahina)\b", lower) or re.search(r"(?:पिछले\s+महीने|पिछला\s+महीना|गत\s+माह|पूर्व\s+माह)", lower):
            return IntentClassificationResult(
                category=IntentCategory.ANALYTICS_EXPLORER,
                confidence=0.96,
                intent_name="category_breakdown",
                target_tool="get_category_breakdown",
                extracted_args={"period": "previous_month"},
                rationale="User requested spending breakdown for the previous month.",
            )

        if (re.search(r"\b(?:this\s+month|current\s+month|is\s+mahine|iss\s+mahine)\b", lower) or re.search(r"(?:इस\s+महीने|इस\s+माह|चालू\s+माह)", lower)) and not any(w in lower for w in ("plan", "forecast", "future", "predict", "योजना", "भविष्य")):
            return IntentClassificationResult(
                category=IntentCategory.ANALYTICS_EXPLORER,
                confidence=0.95,
                intent_name="category_breakdown",
                target_tool="get_category_breakdown",
                extracted_args={"period": "current_month"},
                rationale="User requested spending breakdown for the current month.",
            )

        # -----------------------------------------------------------------
        # TIER 5: Fast Semantic & BM25 Hybrid Tool Retrieval Fallback
        # -----------------------------------------------------------------
        # Run semantic cluster lookup before blind conversational fallback
        active_top = working_memory.active_topic if working_memory else None
        sem_res = FastSemanticClassifier.classify_with_fallback(query, active_top)
        if sem_res:
            sem_cat, sem_conf, sem_intent, sem_tool, sem_args = sem_res
            return IntentClassificationResult(
                category=IntentCategory(sem_cat),
                confidence=sem_conf,
                intent_name=sem_intent,
                target_tool=sem_tool,
                extracted_args=sem_args,
                rationale=f"Semantic cluster matched intent '{sem_intent}' with confidence {sem_conf:.2f}.",
            )

        # Check BM25 hybrid tool retriever before blind financial fallback
        bm25_matches = bm25_retriever.retrieve(query, top_k=1, threshold=1.5)
        if bm25_matches:
            top_tool, top_score = bm25_matches[0]
            TOOL_CATEGORY_MAP = {
                "get_spending_summary": IntentCategory.ANALYTICS_EXPLORER,
                "get_category_breakdown": IntentCategory.ANALYTICS_EXPLORER,
                "compare_periods": IntentCategory.ANALYTICS_EXPLORER,
                "get_top_merchants": IntentCategory.ANALYTICS_EXPLORER,
                "get_payment_mode_summary": IntentCategory.ANALYTICS_EXPLORER,
                "get_recurring_payments": IntentCategory.CASHFLOW_OBLIGATIONS,
                "get_liquidity_buffer": IntentCategory.CASHFLOW_OBLIGATIONS,
                "get_forecast": IntentCategory.CASHFLOW_OBLIGATIONS,
                "get_budget_status": IntentCategory.PREDICTIVE_ADVISORY,
                "simulate_spending_reduction": IntentCategory.PREDICTIVE_ADVISORY,
                "simulate_savings_goal": IntentCategory.PREDICTIVE_ADVISORY,
                "prepare_set_budget": IntentCategory.OPERATIONAL_ACTION,
                "prepare_create_goal": IntentCategory.OPERATIONAL_ACTION,
                "find_unusual_transactions": IntentCategory.FORENSIC_ANOMALY,
                "fetch_portal_receipt_forensics": IntentCategory.PORTAL_AUTOMATION,
                "verify_utility_portal_bill": IntentCategory.PORTAL_AUTOMATION,
                "dispatch_slack_alert": IntentCategory.OPERATIONAL_ACTION,
            }
            mapped_cat = TOOL_CATEGORY_MAP.get(top_tool, IntentCategory.ANALYTICS_EXPLORER)
            extracted_args = {}
            if top_tool == "fetch_portal_receipt_forensics":
                m = "Croma" if ("croma" in lower or "क्रोमा" in lower) else "Swiggy"
                extracted_args = {"merchant": m, "order_id": "order-49102" if m == "Croma" else "order-89218"}
            elif top_tool == "verify_utility_portal_bill":
                extracted_args = {"consumer_id": "102938475"}
            return IntentClassificationResult(
                category=mapped_cat,
                confidence=min(0.92, 0.75 + (top_score * 0.02)),
                intent_name=f"bm25_{top_tool}",
                target_tool=top_tool,
                extracted_args=extracted_args,
                rationale=f"BM25 hybrid retriever matched tool '{top_tool}' with score {top_score:.2f}.",
            )

        FINANCIAL_KEYWORDS = (
            "spend", "spent", "spending", "expense", "expenses", "cost", "costs",
            "buy", "bought", "purchase", "purchases", "order", "orders",
            "money", "cash", "rupee", "rupees", "rs", "inr", "balance", "liquid",
            "budget", "budgets", "cap", "limit", "bill", "bills", "recurring",
            "subscription", "autopay", "due", "afford", "anomaly", "anomalies",
            "fraud", "unusual", "irregular", "payment", "upi", "merchant", "merchants",
            "account", "bank", "save", "saving", "savings", "goal", "goals",
            "forecast", "prediction", "predict", "trajectory", "debt", "loan", "rent",
            "swiggy", "zomato", "croma", "netflix", "bescom", "airtel",
            "kharch", "kharcha", "kharche", "paisa", "paise", "bachat", "kamai",
            "ledger", "transactions", "statement", "finance", "finances",
            # Devanagari script financial keywords (removed bare बताओ / दिखाओ)
            "खर्च", "खर्चा", "खर्चे", "पैसे", "पैसा", "रुपये", "रुपया", "बचत", "कमाई",
            "खाता", "लेनदेन", "बिल", "बजट", "सुरक्षित", "रेंज", "अनियमित", "धोखाधड़ी",
            "वेतन", "किस्त", "बकाया", "जमा", "निकासी", "व्यय", "ब्यौरा",
        )
        has_financial_term = any(w in lower for w in FINANCIAL_KEYWORDS)

        if not has_financial_term:
            return IntentClassificationResult(
                category=IntentCategory.GREETING_AND_META,
                confidence=0.88,
                intent_name="conversational_guidance",
                target_tool=None,
                rationale="Query contains no explicit financial terminology; routed to conversational guidance agent to assist user without executing unprompted calculations.",
            )

        # Default Fallback for general financial inquiries:
        return IntentClassificationResult(
            category=IntentCategory.ANALYTICS_EXPLORER,
            confidence=0.75,
            intent_name="financial_overview",
            target_tool="get_spending_summary",
            extracted_args={"period": "current_month"},
            rationale="General financial inquiry. Querying high-level spending summary and liquid balances.",
        )

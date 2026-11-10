"""
Fast Semantic Intent Classifier for FinSight Voice Agent.
Performs lightweight semantic intent classification for queries where
deterministic regex confidence is < 0.8, preventing blind fallbacks
to conversational greetings or recurring bill dumps.
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple
from backend.app.voice_agent.session_state import ActiveTopic

logger = logging.getLogger(__name__)


class FastSemanticClassifier:
    """
    Lightweight, deterministic semantic intent classifier based on
    anchor centroids and semantic cluster token sets.
    """

    INTENT_CLUSTERS = {
        "liquidity_safety_buffer": {
            "category": "cashflow_obligations",
            "target_tool": "get_liquidity_buffer",
            "topic_affinity": ActiveTopic.CASHFLOW_LIQUIDITY,
            "anchor_tokens": {
                "range", "buffer", "safe", "runway", "reserve", "emergency", "surplus",
                "coverage", "months", "liquid", "liquidity", "suraksha", "bache", "kitna safe",
                "रेंज", "बफर", "सेफ", "सुरक्षित", "सुरक्षा", "रनवे", "रिजर्व", "बचत", "कवर",
            },
            "phrases": [
                "range kitna hai", "range kya hai", "kitna range", "safe range",
                "kitna safe hai", "buffer kitna", "emergency fund kitna", "cash runway",
                "मेरा safe range बताओ", "सेफ रेंज क्या है", "सुरक्षा बफर कितना है", "रनवे कितना है", "safe range batao",
            ],
        },
        "cashflow_forecast": {
            "category": "cashflow_obligations",
            "target_tool": "get_forecast",
            "topic_affinity": ActiveTopic.CASHFLOW_LIQUIDITY,
            "anchor_tokens": {
                "future", "forecast", "predict", "prediction", "trajectory", "ahead",
                "projection", "agle mahine", "aage kya hoga", "bhavishya",
                "भविष्य", "अनुमान", "आगे", "पूर्वानुमान",
            },
            "phrases": [
                "future predictions", "what are my future predictions", "cashflow forecast",
                "future trajectory", "predict my cashflow", "आगे का अनुमान", "कैशफ्लो कैसा रहेगा",
            ],
        },
        "compare_periods": {
            "category": "analytics_explorer",
            "target_tool": "compare_periods",
            "topic_affinity": ActiveTopic.SPEND_ANALYSIS,
            "anchor_tokens": {
                "increase", "spike", "jump", "surge", "higher", "rose", "growth",
                "badha", "badh", "kyun", "kyu", "diff", "difference", "variance",
                "बढ़ा", "वृद्धि", "ज्यादा", "अधिक", "क्यों", "तुलना", "अंतर",
            },
            "phrases": [
                "why did spending increase", "spend spike", "kharch kyu badha", "why spend jumped",
                "खर्च क्यों बढ़ा", "खर्चा ज्यादा क्यों हुआ",
            ],
        },
        "category_breakdown": {
            "category": "analytics_explorer",
            "target_tool": "get_category_breakdown",
            "topic_affinity": ActiveTopic.SPEND_ANALYSIS,
            "anchor_tokens": {
                "breakdown", "category", "categories", "where", "spend", "spent", "distribution",
                "kahan gaya", "kitna kharcha", "kharcha kidhar",
                "खर्च", "खर्चा", "खर्चे", "व्यय", "पिछले", "पिछला", "महीना", "महीने", "ब्यौरा", "वितरण", "श्रेणी", "बताओ",
            },
            "phrases": [
                "spending breakdown", "last month", "previous month", "kahan gaya paisa",
                "पिछले महीने का खर्चा बताओ", "पिछला महीना", "खर्चा बताओ", "कहाँ गया पैसा",
            ],
        },
        "detect_anomalies": {
            "category": "forensic_anomaly",
            "target_tool": "find_unusual_transactions",
            "topic_affinity": ActiveTopic.ANOMALIES,
            "anchor_tokens": {
                "anomaly", "anomalies", "unusual", "suspicious", "irregular", "fraud",
                "weird", "strange", "gadbad", "galat", "sandigdh", "alert", "outlier",
                "गड़बड़", "गलत", "असामान्य", "संदिग्ध", "धोखाधड़ी", "फ्रॉड", "अलर्ट",
            },
            "phrases": [
                "check anomalies", "unusual transactions", "kuch gadbad", "fraud transactions",
                "कोई गड़बड़ लेनदेन", "संदिग्ध खर्चे",
            ],
        },
        "generate_budget_plan": {
            "category": "predictive_advisory",
            "target_tool": "get_budget_plan",
            "topic_affinity": ActiveTopic.BUDGETING,
            "anchor_tokens": {
                "budget", "plan", "recommend", "allocation", "banao", "strategy", "cap",
                "बजट", "प्लान", "योजना", "बनाओ", "नया बजट",
            },
            "phrases": [
                "prepare budget plan", "plan my budget", "budget banao", "next month plan",
                "बजट बनाओ", "अगले महीने का बजट", "खर्च की योजना",
            ],
        },
        "upcoming_bills": {
            "category": "cashflow_obligations",
            "target_tool": "get_recurring_payments",
            "topic_affinity": ActiveTopic.BILLS_COMMITMENTS,
            "anchor_tokens": {
                "bill", "bills", "recurring", "subscription", "autopay", "netflix", "rent",
                "bescom", "airtel", "due", "commitment", "commitments",
                "बिल", "किस्त", "सब्सक्रिप्शन", "देय", "भुगतान",
            },
            "phrases": [
                "upcoming bills", "due bills", "bill payments", "recurring subscriptions",
                "आने वाले बिल", "कौन से बिल भरने हैं",
            ],
        },
    }

    @classmethod
    def classify_with_fallback(
        cls,
        query: str,
        active_topic: Optional[ActiveTopic] = None,
    ) -> Optional[Tuple[str, float, str, str, Dict[str, Any]]]:
        """
        Calculates cluster similarity scores.
        Returns: (category, confidence, intent_name, target_tool, extracted_args) or None.
        """
        raw = query.lower().strip()
        tokens = set(re.findall(r"\w+", raw))
        if not tokens:
            return None

        best_score = 0.0
        best_intent = None
        best_meta = None

        for intent_name, meta in cls.INTENT_CLUSTERS.items():
            anchors = meta["anchor_tokens"]
            phrases = meta["phrases"]

            # Exact phrase match gives immediate high confidence
            for ph in phrases:
                if ph in raw:
                    return (
                        meta["category"],
                        0.94,
                        intent_name,
                        meta["target_tool"],
                        {},
                    )

            # Token overlap score (Jaccard-like)
            overlap = tokens.intersection(anchors)
            score = len(overlap) / max(len(tokens), 1)

            # Active topic affinity boost (+0.30)
            if active_topic and meta.get("topic_affinity") == active_topic and overlap:
                score += 0.30

            if score > best_score:
                best_score = score
                best_intent = intent_name
                best_meta = meta

        # Minimum semantic match threshold
        if best_score >= 0.25 and best_intent and best_meta:
            confidence = min(0.92, 0.75 + (best_score * 0.2))
            return (
                best_meta["category"],
                round(confidence, 2),
                best_intent,
                best_meta["target_tool"],
                {},
            )

        return None

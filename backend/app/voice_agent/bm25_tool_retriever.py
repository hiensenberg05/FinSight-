"""
BM25 Hybrid Tool Retriever for FinSight Voice Agent.
Indexes deterministic financial tool schemas and domain lexicons
to dynamically rank and retrieve the top candidate tools for single-hop
and multi-hop conversational financial queries.
"""

import math
import re
from typing import Dict, Any, List, Optional, Tuple, Set
from backend.app.voice_agent.tool_definitions import TOOL_DEFINITIONS

# Bilingual synonym mapping to enrich tool representations
TOOL_SYNONYMS: Dict[str, List[str]] = {
    "get_spending_summary": [
        "income", "earnings", "salary", "expense", "expenses", "spend", "net savings",
        "balance", "liquid balance", "financial overview", "summary", "health score",
        "kamai", "aamdani", "kul kharcha", "kul bachat", "bachat", "kitna bacha", "kaisa chal raha hai",
        "कमाई", "वेतन", "कुल खर्च", "बचत", "खाता बैलेंस", "अवलोकन", "कैसा चल रहा है",
    ],
    "get_category_breakdown": [
        "category", "categories", "breakdown", "distribution", "split", "drill down",
        "shopping", "food", "dining", "groceries", "travel", "entertainment", "where spent", "where money went",
        "kahan gaya", "kidhar kharch hua", "kis category me", "pichla mahina", "pichle mahine ka kharcha",
        "श्रेणी", "कैटेगरी", "खर्च ब्यौरा", "कहाँ खर्च हुआ", "पिछले महीने का खर्चा", "वितरण",
    ],
    "compare_periods": [
        "compare", "comparison", "difference", "delta", "spike", "jump", "increase",
        "why increase", "why spent more", "variance", "growth", "rose", "higher",
        "kyun badha", "kyu badha", "kharch kyu badha", "zyada kyu hua", "tulna", "farq",
        "तुलना", "खर्च क्यों बढ़ा", "खर्चा ज्यादा क्यों हुआ", "अंतर", "वृद्धि", "स्पाइक",
    ],
    "get_top_merchants": [
        "merchant", "merchants", "vendor", "vendors", "counterparty", "shop", "stores",
        "top spend", "most frequent", "swiggy", "zomato", "amazon", "flipkart",
        "dukaan", "store", "kahan sabse zyada", "sabse zyada kharcha",
        "दुकानदार", "मर्चेंट", "सबसे ज्यादा खर्च", "दुकान",
    ],
    "get_payment_mode_summary": [
        "payment mode", "mode", "method", "upi", "card", "credit card", "debit card",
        "netbanking", "gpay", "phonepe", "paytm",
        "kis mode se", "kaise pay kiya", "online payment",
        "पेमेंट मोड", "यूपीआई", "कार्ड", "नेटबैंकिंग",
    ],
    "get_recurring_payments": [
        "recurring", "subscription", "subscriptions", "autopay", "bill", "bills",
        "due", "due dates", "upcoming bills", "rent", "electricity", "bescom", "airtel", "netflix",
        "aane wale bill", "bijli ka bill", "kiraya", "kist", "kab bharna hai",
        "बिल", "आने वाले बिल", "किस्त", "सब्सक्रिप्शन", "किराया", "बिजली", "देय",
    ],
    "get_liquidity_buffer": [
        "buffer", "safe range", "safety cushion", "runway", "liquid", "reserve", "emergency fund",
        "how safe", "afford", "safety net", "coverage", "months of runway",
        "safe range kitna hai", "suraksha", "kitna safe hoon", "bachao", "emergency cushion",
        "सेफ रेंज", "बफर", "सुरक्षित", "रनवे", "इमरजेंसी फंड", "सुरक्षा", "कवर",
    ],
    "get_budget_status": [
        "budget", "budget status", "budget limit", "cap", "utilization", "over budget",
        "alert", "threshold", "exceeded", "dining alert", "swiggy limit",
        "budget kitna hai", "limit cross", "alert aaya", "kharch limit",
        "बजट", "बजट लिमिट", "कैप", "अलर्ट", "सीमा", "खर्च सीमा",
    ],
    "get_forecast": [
        "forecast", "predict", "prediction", "trajectory", "future", "projection",
        "next month", "upcoming months", "holt winters",
        "aage ka anuman", "bhavishya", "agle mahine kya hoga", "future me kitna bachega",
        "पूर्वानुमान", "भविष्य", "अनुमान", "आगे का खर्च", "प्रोजेक्शन",
    ],
    "find_unusual_transactions": [
        "unusual", "anomaly", "anomalies", "suspicious", "flagged", "irregular", "fraud",
        "outlier", "croma", "large transaction", "odd",
        "gadbad", "galat", "sandigdh", "koi jhol", "kuch galat kata",
        "असामान्य", "संदिग्ध", "गड़बड़", "फ्रॉड", "धोखाधड़ी", "अलर्ट",
    ],
    "simulate_spending_reduction": [
        "simulate", "reduction", "cut", "reduce", "save more", "what if", "curb",
        "discretionary", "what if i cut", "spending cut", "velocity",
        "agar kam karein", "bachat badhana", "agar 20% kam karein", "cut karein toh",
        "कटौती", "बचत बढ़ाएं", "कम करें", "अगर कम करें", "सिमुलेशन",
    ],
    "simulate_savings_goal": [
        "goal", "savings goal", "milestone", "vacation fund", "car fund", "target date",
        "reach goal", "accelerate goal", "completion date",
        "lakshya", "goal kab tak hoga", "vacation fund kab pura hoga",
        "लक्ष्य", "बचत लक्ष्य", "वेकेशन फंड", "कब पूरा होगा",
    ],
    "prepare_set_budget": [
        "set budget", "cap category", "modify budget", "set limit", "lock budget",
        "budget lagao", "cap set karo", "limit baandho",
        "बजट सेट करो", "कैप लगाओ", "सीमा तय करो",
    ],
    "prepare_create_goal": [
        "create goal", "start goal", "new savings goal", "create vacation fund",
        "naya goal banao", "goal shuru karo",
        "नया लक्ष्य बनाओ", "लक्ष्य शुरू करो",
    ],
    "fetch_portal_receipt_forensics": [
        "receipt", "invoice", "itemized", "order items", "swiggy receipt", "swiggy bill",
        "croma receipt", "croma invoice", "bill details", "breakdown of order", "hidden fees",
        "surge fee", "delivery charges", "packaging fee", "show receipt", "open receipt", "inspect receipt",
        "swiggy ka bill", "order me kya tha", "bill dikhao", "receipt dikhao", "kya mangwaya tha",
        "रसीद", "बिल", "ऑर्डर ब्यौरा", "रसीद दिखाओ", "स्विगी रसीद", "आइटम डिटेल्स",
    ],
    "verify_utility_portal_bill": [
        "verify bill", "portal verification", "bescom portal", "check portal", "live meter",
        "units consumed", "kwh", "meter reading", "official portal", "verify on site", "live bill status",
        "portal pe verify", "bijli bill portal", "meter check", "live portal check", "portal check karo",
        "पोर्टल वेरिफिकेशन", "बिजली बिल पोर्टल", "मीटर रीडिंग", "पोर्टल पर चेक",
    ],
    "dispatch_slack_alert": [
        "slack", "slack alert", "send to slack", "post on slack", "slack notification",
        "slack pe bhejo", "slack par bhej do", "slack message", "channel alert",
        "slack alert set", "slack alert chahiye", "slack integration", "send test alert",
        "स्लैक", "स्लैक अलर्ट", "स्लैक पर भेजो", "स्लैक नोटिफिकेशन",
    ],
}


class BM25ToolRetriever:
    """
    Okapi BM25 implementation optimized for deterministic financial tool selection.
    Indexes tool descriptions, parameters, and bilingual Indian English / Hindi aliases.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: Dict[str, List[str]] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.avg_doc_len: float = 0.0
        self.df: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.total_docs: int = 0
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r"[^\w\s₹]", " ", text.lower())
        tokens = [tok for tok in cleaned.split() if len(tok) >= 2]
        return tokens

    def _build_index(self):
        docs: Dict[str, List[str]] = {}
        for tool in TOOL_DEFINITIONS:
            name = tool["name"]
            desc = tool.get("description", "")
            params = tool.get("parameters", {}).get("properties", {})
            param_tokens = []
            for p_name, p_body in params.items():
                param_tokens.append(p_name)
                param_tokens.extend(self._tokenize(p_body.get("description", "")))

            synonyms = TOOL_SYNONYMS.get(name, [])
            combined_text = f"{name} {desc} {' '.join(param_tokens)} {' '.join(synonyms)}"
            docs[name] = self._tokenize(combined_text)

        # Include liquidity buffer explicitly if missing from TOOL_DEFINITIONS
        if "get_liquidity_buffer" not in docs:
            docs["get_liquidity_buffer"] = self._tokenize(
                "get_liquidity_buffer Calculates cash runway, safety buffer months, liquid reserve vs monthly fixed commitments "
                + " ".join(TOOL_SYNONYMS.get("get_liquidity_buffer", []))
            )

        self.corpus = docs
        self.total_docs = len(docs)
        self.doc_lengths = {name: len(tokens) for name, tokens in docs.items()}
        self.avg_doc_len = sum(self.doc_lengths.values()) / max(self.total_docs, 1)

        # Document Frequency
        for tokens in docs.values():
            unique_terms = set(tokens)
            for term in unique_terms:
                self.df[term] = self.df.get(term, 0) + 1

        # Inverse Document Frequency (with floor of 0.0)
        for term, freq in self.df.items():
            idf_val = math.log((self.total_docs - freq + 0.5) / (freq + 0.5) + 1.0)
            self.idf[term] = max(0.1, idf_val)

    def score_query(self, query: str) -> Dict[str, float]:
        q_tokens = self._tokenize(query)
        scores: Dict[str, float] = {name: 0.0 for name in self.corpus}
        if not q_tokens:
            return scores

        for term in q_tokens:
            if term not in self.idf:
                continue
            term_idf = self.idf[term]
            for doc_name, doc_tokens in self.corpus.items():
                tf = doc_tokens.count(term)
                if tf == 0:
                    continue
                d_len = self.doc_lengths[doc_name]
                denom = tf + self.k1 * (1.0 - self.b + self.b * (d_len / self.avg_doc_len))
                term_score = term_idf * (tf * (self.k1 + 1.0)) / denom
                scores[doc_name] += term_score

        return scores

    def retrieve(self, query: str, top_k: int = 3, threshold: float = 0.5) -> List[Tuple[str, float]]:
        scores = self.score_query(query)
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [(name, round(score, 3)) for name, score in ranked[:top_k] if score >= threshold]

    def detect_multi_intent(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Detects if query contains dual intent spanning two distinct financial tools.
        Example: 'Why did my spending increase and can I pay my upcoming bills?'
        Returns: (primary_tool, secondary_tool) or (primary_tool, None).
        """
        ranked = self.retrieve(query, top_k=4, threshold=0.6)
        if not ranked:
            return None, None

        primary_tool, primary_score = ranked[0]
        secondary_tool = None

        # Check if a secondary tool has strong signals from a distinct cluster
        TOOL_CLUSTERS = {
            "spend_analytics": {"get_category_breakdown", "compare_periods", "get_top_merchants", "get_spending_summary"},
            "commitments_bills": {"get_recurring_payments"},
            "liquidity_runway": {"get_liquidity_buffer", "get_forecast"},
            "advisory_budget": {"get_budget_status", "simulate_spending_reduction", "simulate_savings_goal", "prepare_set_budget"},
            "anomaly_forensics": {"find_unusual_transactions"},
        }

        def get_cluster(tool: str) -> Optional[str]:
            for cluster_name, tools in TOOL_CLUSTERS.items():
                if tool in tools:
                    return cluster_name
            return None

        primary_cluster = get_cluster(primary_tool)

        for candidate, cand_score in ranked[1:]:
            cand_cluster = get_cluster(candidate)
            # If candidate belongs to a different domain cluster and has meaningful score
            if cand_cluster and cand_cluster != primary_cluster and cand_score >= 1.2:
                secondary_tool = candidate
                break

        return primary_tool, secondary_tool


# Global singleton instance for fast reuse
bm25_retriever = BM25ToolRetriever()

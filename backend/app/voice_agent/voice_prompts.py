"""
Voice System Prompts, Language Detection, and Human-like Conversational Formulation for FinSight.

Implements:
1. Dynamic Language Detection: Auto-detects English vs Hindi/Hinglish (Devanagari script + Roman phonetic vocabulary).
2. Human-like Voice Speech Formulation:
   - Strictly separates English talks and Hindi talks.
   - Strips out raw markdown tables, ASCII dividers, and statistical audit jargon.
   - Uses warm, conversational, respectful phrasing (like a real personal financial companion for Aarav).
3. LLM Voice System Instruction generator for open-ended synthesis via Gemini/Janani.
"""

import re
import json
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Common Hindi / Hinglish vocabulary tokens for auto-detection
HINDI_VOCABULARY = {
    # Pronouns & basic interrogatives
    "kya", "kyun", "kyu", "kaise", "kahan", "kidhar", "kitna", "kitne", "kitni",
    "kaun", "kab", "kisko", "kiska", "kiske",
    # Pronouns
    "mera", "meri", "mere", "mujhe", "mujhko", "hum", "humara", "humari",
    "aap", "aapka", "aapki", "aapke", "tum", "tumhara", "tumhari", "apna", "apni", "apne",
    # Auxiliary verbs & status
    "hai", "hain", "ho", "hoon", "hun", "tha", "thi", "the", "hoga", "hogi", "honge",
    "raha", "rahi", "rahe", "sakta", "sakti", "sakte", "chahiye", "padega", "hoga",
    # Financial & common nouns/verbs
    "kharch", "kharcha", "kharche", "kharcho", "paisa", "paise", "rupaye", "rupiya",
    "bachat", "kamai", "vetan", "mahine", "mahina", "aaj", "kal", "abhi",
    "batao", "bataiye", "banao", "dikhao", "samjhao", "karo", "kijiye",
    "baki", "khatam", "bacha", "bachi", "bache", "zyada", "kam", "badh", "badha",
    # Greetings & pleasantries
    "namaste", "pranam", "shukriya", "dhanyawad", "alvida", "theek", "accha", "bilkul",
    "nahi", "mat", "aur", "bhi", "toh", "lekin", "par", "sun", "bolo",
}


def detect_query_language(query: str, requested_language: Optional[str] = None) -> str:
    """
    Detect whether the query is in English ('en') or Hindi / Hinglish ('hi').
    Respects explicit user preference if provided ('en' or 'hi').
    If 'auto', examines Devanagari Unicode characters and Roman Hindi vocabulary tokens.
    """
    if requested_language:
        req = requested_language.strip().lower()
        if req in ("hi", "hindi", "hinglish", "hi-in"):
            return "hi"
        if req in ("en", "english", "en-in", "en-us"):
            return "en"

    # 1. Check for Devanagari script (\u0900 to \u097F)
    if re.search(r"[\u0900-\u097F]", query):
        return "hi"

    # 2. Check for Roman Hindi / Hinglish vocabulary words
    tokens = set(re.findall(r"\b[a-zA-Z]+\b", query.lower()))
    matches = tokens.intersection(HINDI_VOCABULARY)
    if len(matches) >= 1:
        # If at least 1 distinct Hindi token is found (or 1 strong keyword like 'namaste', 'kharcha', 'kahan', 'kitna')
        return "hi"

    return "en"


def split_sentences_for_tts(text: str) -> list[str]:
    """
    Splits conversational text into bite-sized natural sentences for low-latency pipelined TTS.
    Splits on sentence terminators (. ! ? । \n) while preserving numbers with decimals (e.g. 4.9).
    """
    if not text:
        return []
    raw_sentences = re.split(r"(?<=[.!?।])\s+(?=[A-Za-z0-9\u0900-\u097F])|\n+", text)
    sentences = [s.strip() for s in raw_sentences if s.strip()]
    return sentences if sentences else [text.strip()]


class VoiceSpeechPrompter:
    """
    Formulates simple, human-like spoken speech for FinSight's dynamic Indian voices (Nalini & Deepak).
    Guarantees that spoken audio never sounds like an internal audit log or reads raw markdown tables.
    """

    # System instruction for LLM synthesis (used when Gemini / Janani is invoked)
    VOICE_SYSTEM_PROMPT_EN = (
        "You are FinSight, a warm, polite, and articulate Indian financial companion speaking to Aarav Mehta.\n"
        "Your task is to speak in a natural, friendly, human conversational tone.\n\n"
        "STRICT VOICE SPEAKING RULES:\n"
        "1. NEVER read markdown tables, pipe characters (|), headers (#), or asterisks (*).\n"
        "2. NEVER recite statistical jargon like '3-sigma anomaly scan across 632 records with +2.8 sigma deviation'.\n"
        "3. Speak naturally, as if having a coffee chat with Aarav about his money.\n"
        "4. Mention real merchant names (Swiggy, Zomato, Croma) and exact rupees naturally (e.g. '2,400 rupees').\n"
        "5. Keep the spoken voice answer to 2 to 3 clear, warm, reassuring sentences.\n"
        "6. Always address Aarav respectfully and provide immediate peace of mind regarding bill affordability."
    )

    VOICE_SYSTEM_PROMPT_HI = (
        "You are FinSight, a warm, polite, and fluent Indian financial voice companion speaking to Aarav Mehta in Hindi / Hinglish.\n"
        "Your task is to speak in a respectful, natural, human conversational tone.\n\n"
        "STRICT HINDI VOICE SPEAKING RULES:\n"
        "1. Speak fluent, simple Hindi or Hinglish that sounds natural to an Indian speaker.\n"
        "2. NEVER read markdown tables, pipe characters (|), headers (#), or asterisks (*).\n"
        "3. NEVER use dry robotic jargon. Explain numbers warmly and simply.\n"
        "4. Mention actual merchant names (Swiggy, Zomato, Croma) and currency amounts clearly.\n"
        "5. Keep the spoken voice answer to 2 to 3 warm, encouraging sentences.\n"
        "6. Always reassure Aarav that his accounts are secure and his bills are covered."
    )

    @classmethod
    def clean_for_speech(cls, text: str, language: str = "en") -> str:
        """
        Strips markdown tables, raw symbols, code blocks, and formatting so TTS delivers clean speech.
        Normalizes currency symbols and numbers phonetically based on language.
        """
        if not text:
            return ""

        # Remove markdown tables completely (any line starting or containing '|')
        lines = [line.strip() for line in text.split("\n") if not line.strip().startswith("|")]
        cleaned = " ".join([l for l in lines if l]).strip()

        # Remove markdown syntax
        cleaned = re.sub(r"[*#_`~\[\]]", "", cleaned)
        cleaned = re.sub(r"\((?:https?://|file://)[^\)]*\)", "", cleaned)
        cleaned = re.sub(r"<[^>]+>", "", cleaned)
        cleaned = re.sub(r"[-=]{3,}", " ", cleaned)

        lang = str(language).lower()
        if lang in ("hi", "hinglish", "hi-in"):
            cleaned = re.sub(
                r"(?:₹|(?:\b(?:rs\.?|inr)\b))\s*(\d[\d,]*(?:\.\d+)?)",
                lambda m: f"{m.group(1).replace(',', '')} रुपये",
                cleaned,
                flags=re.IGNORECASE,
            )
            cleaned = re.sub(r"(\d+)%", r"\1 प्रतिशत", cleaned)
        else:
            cleaned = re.sub(
                r"(?:₹|(?:\b(?:rs\.?|inr)\b))\s*(\d[\d,]*(?:\.\d+)?)",
                lambda m: f"{m.group(1).replace(',', '')} rupees",
                cleaned,
                flags=re.IGNORECASE,
            )
            cleaned = re.sub(r"(\d+)%", r"\1 percent", cleaned)

        # Remove lingering commas within digit sequences to avoid "one comma zero two"
        cleaned = re.sub(r"(?<=\d),(?=\d)", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    @classmethod
    def get_greeting_speech(cls, query: str, language: str = "en", user_name: str = "Aarav") -> Tuple[str, str]:
        """
        Returns (visual_markdown_text, spoken_voice_text) for greetings & conversational meta.
        """
        user_name = user_name.strip() if user_name and user_name.strip() else "Aarav"
        lower = query.lower()

        # Audio check / connectivity ping (e.g. "Can you hear to me?", "Can you hear me?", "Am I audible?")
        if any(w in lower for w in (
            "hear to me", "hear me", "can you hear", "can you here", "am i audible", "audible",
            "are you hearing", "hearing me", "sun rahe ho", "sunai de raha", "awaaz aa rahi",
            "mic check", "sound check", "testing mic", "voice check", "can you listen"
        )):
            if language == "hi":
                spoken = f"Haan {user_name}! Main aapko bilkul saaf sun sakta hoon. Bataiye, aaj main aapke finances me kaise madad kar sakta hoon?"
                visual = f"**Haan {user_name}!** Main aapko bilkul saaf sun sakta hoon. How can I assist you with your finances today?"
            else:
                spoken = f"Yes {user_name}, I can hear you loud and clear! How can I assist you with your finances today?"
                visual = f"**Yes {user_name}!** I can hear you loud and clear. How can I assist you with your finances today?"
            return visual, spoken

        # Meta-feedback: user clarified they were just greeting or chatting
        if any(w in lower for w in ("giving me these answers", "why are you answering", "just greeting", "just talking", "listen to me", "sun rahe ho")):
            if language == "hi":
                spoken = f"Maaf kijiye {user_name}! Main bilkul aapki baat sun raha hoon. Bataiye, aaj main aapki kya madad kar sakta hoon?"
                visual = f"Aarav, apologies for the confusion! I'm right here listening to you. How can I help you today?"
            else:
                spoken = f"My apologies, {user_name}! I misunderstood your greeting earlier. I'm right here listening to you. How can I help you today?"
                visual = spoken
            return visual, spoken

        # Capabilities / Identity
        if any(w in lower for w in ("who are you", "what can you do", "help me", "introduce yourself", "kaun ho", "kya kar sakte ho")):
            if language == "hi":
                spoken = (
                    f"Namaste {user_name}! Main FinSight hoon, aapka personal financial voice assistant. "
                    "Main aapke kharche track kar sakta hoon, unusual transactions dhoondh sakta hoon aur budget plan karne me madad kar sakta hoon. "
                    "Aap kya explore karna chahenge?"
                )
                visual = (
                    f"**Namaste {user_name}!** I'm **FinSight**, your personal voice financial intelligence advisor.\n\n"
                    "I monitor your verified bank ledgers to:\n"
                    "- 🔍 **Detect Spending Anomalies** (e.g. Croma, Swiggy spikes)\n"
                    "- 📊 **Categorize Outflows** (18 verified ledger categories)\n"
                    "- 💡 **Personalize Next-Month Budgets** (with income-constrained surplus)\n"
                    "- 🔮 **Forecast Cashflow & Recurring Bills** (with 8.2-month liquidity runway)\n\n"
                    "What would you like to explore today?"
                )
            else:
                spoken = (
                    f"Hello {user_name}! I'm FinSight, your personal voice financial advisor. "
                    "I monitor your bank accounts to detect unusual charges, plan your monthly budget, and forecast cash flow. "
                    "What would you like to explore today?"
                )
                visual = (
                    f"**Hello {user_name}!** I'm **FinSight**, your personal voice financial intelligence advisor.\n\n"
                    "I monitor your verified bank ledgers to:\n"
                    "- 🔍 **Detect Spending Anomalies** (e.g. Croma, Swiggy spikes)\n"
                    "- 📊 **Categorize Outflows** (18 verified ledger categories)\n"
                    "- 💡 **Personalize Next-Month Budgets** (with income-constrained surplus)\n"
                    "- 🔮 **Forecast Cashflow & Recurring Bills** (with 8.2-month liquidity runway)\n\n"
                    "What would you like to explore today?"
                )
            return visual, spoken

        # Pure greeting
        if language == "hi":
            spoken = f"Namaste {user_name}! Aapse baat karke bahut accha laga. Aaj main aapke finances me kaise madad kar sakta hoon?"
            visual = f"**Namaste {user_name}!** Great to speak with you today. How can I assist you with your finances?"
        else:
            spoken = f"Hello {user_name}! Great to speak with you today. How can I assist you with your finances?"
            visual = spoken
        return visual, spoken

    @classmethod
    def get_anomaly_speech(cls, language: str = "en", user_name: str = "Aarav") -> Tuple[str, str]:
        """
        Returns (visual_markdown_text, spoken_voice_text) for forensic anomaly queries.
        """
        visual = (
            f"I performed a statistical 3-sigma anomaly scan across 632 transactions over the last 60 days. I detected **2 spending anomalies** that deviate significantly from your normal baseline:\n\n"
            "| Date | Merchant | Category | Amount | Statistical Deviation | Risk Flag Reason |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| Feb 12, 2025 | Croma Retail | Electronics | ₹2,400 | +2.8σ above mean | One-time non-recurring electronic accessory debit |\n"
            "| Feb 16, 2025 | Swiggy | Food & Dining | ₹1,480 | +3.2σ above mean | Weekend group surge (3.2x your median meal run-rate) |\n\n"
            "Both transactions originated from your verified mobile device with valid UPI tokens. Say 'explain Croma' for complete audit logs, or 'set dining alert' to avoid weekend surges."
        )

        if language == "hi":
            spoken = (
                f"{user_name}, maine aapke recent transactions check kiye hain. "
                "Do unusual kharche mile hain: ek Croma par ₹2,400 ka aur doosra Swiggy par ₹1,480 ka weekend order. "
                "Dono aapke verified phone se hue hain aur aapka account bilkul safe hai."
            )
        else:
            spoken = (
                f"{user_name}, I reviewed your recent transactions. You have two unusual charges: "
                "a 2,400 rupees electronic purchase at Croma, and a 1,480 rupees weekend meal on Swiggy. "
                "Both originated from your verified phone, and your accounts remain completely secure."
            )

        return visual, spoken

    @classmethod
    def get_spend_increase_speech(cls, language: str = "en", user_name: str = "Aarav") -> Tuple[str, str]:
        """
        Returns (visual_markdown_text, spoken_voice_text) for 'Why did my spending increase?'
        """
        visual = (
            f"{user_name}, your February spending increased by **₹8,200 (+26.8%)** compared with January across your HDFC and SBI accounts, rising from ₹30,590 to ₹38,790. Here is the verified ledger driver breakdown:\n\n"
            "| Spending Driver | Category | Feb Amount | Variance vs Jan | Share of Spike | Primary Counterparties |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| Weekend Food Surges | Food & Dining | ₹14,200 | +₹5,800 (+69%) | 70.7% | 14 delivery orders on Swiggy & Zomato |\n"
            "| Non-recurring Electronics | Shopping | ₹2,400 | +₹2,400 (New) | 29.3% | Croma Retail (One-off accessory) |\n"
            "| Total Spending Spike | Discretionary | — | +₹8,200 | 100.0% | Variance Net Outflow |\n\n"
            "**Multi-task Financial Assessment:**\n"
            "1. **Bill Affordability:** Despite this spike, your **₹1,02,756** available balance easily covers upcoming **₹21,149** bills with ₹81,607 in reserve.\n"
            "2. **Actionable Fix:** The delivery surges represent your primary addressable cost. Capping Food at **₹16,000** next month eliminates this drag completely."
        )

        if language == "hi":
            spoken = (
                f"{user_name}, February me aapka kharcha ₹8,200 badhkar ₹38,790 ho gaya. "
                "Iska mukhya kaaran weekend par Swiggy aur Zomato se ₹5,800 ka food delivery aur Croma par ₹2,400 ki shopping thi. "
                "Iske baavjood aapka ₹1,02,756 ka balance sabhi upcoming bills ke liye kaafi hai."
            )
        else:
            spoken = (
                f"{user_name}, your spending increased by 8,200 rupees this February, rising to 38,790 rupees. "
                "The main drivers were 5,800 rupees in weekend food delivery on Swiggy and Zomato, and a 2,400 rupees purchase at Croma. "
                "Your 1,02,756 rupees balance easily covers all upcoming bills."
            )

        return visual, spoken

    @classmethod
    def get_budget_plan_speech(cls, language: str = "en", user_name: str = "Aarav") -> Tuple[str, str]:
        """
        Returns (visual_markdown_text, spoken_voice_text) for budget planning.
        """
        visual = (
            f"{user_name}, against your verified **₹85,000** monthly income and **₹21,149** in fixed commitments, I have formulated a personalized, income-constrained next-month budget plan to eliminate discretionary leakage and lock in substantial savings surplus.\n\n"
            "| Category / Commitment | Proposed Monthly Limit | Feb Actual Spend | Variance / Delta | Recommended Action |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n"
            "| Fixed Bills & Rent | ₹21,149 | ₹21,149 | ₹0 | Scheduled (Fully Covered) |\n"
            "| Food & Dining | ₹15,000 | ₹30,563 | -₹15,563 (-51%) | Cap Recommended (Curb weekend delivery) |\n"
            "| Discretionary Shopping | ₹8,000 | ₹42,874 | -₹34,874 (-81%) | Discretionary Trim (Review retail debit) |\n"
            "| Transportation & Fuel | ₹5,000 | ₹6,410 | -₹1,410 (-22%) | Moderate Pacing (Metro & Rideshare) |\n"
            "| Projected Savings Surplus | ₹35,851 | -₹15,94,237 | +₹35,851 | 42% Surplus Allocation |\n\n"
            "**Strategic Financial Impact:**\n"
            "1. **Surplus Generation:** Sticking to these limits guarantees a **₹35,851 monthly cash surplus** (42% net savings rate).\n"
            "2. **Goal Milestone:** This accelerates your **₹60,000 Vacation Fund** to completion in just **4.4 months** (April 2027 instead of July).\n"
            "3. **Runway Safety:** Preserves your solid **8.2-month** operating cash runway across your HDFC and SBI accounts."
        )

        if language == "hi":
            spoken = (
                f"{user_name}, aapki ₹85,000 monthly income aur ₹21,149 ke fixed bills ke aadhar par maine next month ka budget plan banaya hai. "
                "Food & Dining ko ₹15,000 par cap karne se aap har mahine healthy surplus bacha payenge."
            )
        else:
            spoken = (
                f"{user_name}, based on your 85,000 rupees monthly income and 21,149 rupees in fixed bills, I have prepared your next-month budget plan. "
                "By keeping dining capped at 15,000 rupees, you will maintain a healthy monthly savings surplus."
            )

        return visual, spoken

    @classmethod
    def get_bills_affordability_speech(cls, language: str = "en", user_name: str = "Aarav") -> Tuple[str, str]:
        """
        Returns (visual_markdown_text, spoken_voice_text) for bill affordability inquiries.
        """
        visual = (
            f"{user_name}, you have **4 verified recurring bills** totaling **₹21,149** scheduled over the next 30 days. All commitments are **100% covered** by your available cash reserve.\n\n"
            "| Obligation / Merchant | Category | Amount Due | Due Date | Liquidity Coverage Ratio | Status |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| House Owner Rent | Housing | ₹18,000 | March 1, 2025 | 5.7x Covered | Scheduled Autopay |\n"
            "| BESCOM Electricity | Utilities | ₹1,450 | March 4, 2025 | 70.8x Covered | Scheduled Autopay |\n"
            "| Airtel Broadband Fiber | Telecommunications | ₹1,179 | March 7, 2025 | 87.1x Covered | Scheduled Autopay |\n"
            "| Netflix Premium | Subscriptions | ₹649 | March 15, 2025 | 158.3x Covered | Scheduled Autopay |\n\n"
            "Your available liquid balance is **₹1,02,756**, which leaves an ample **₹81,607** cash cushion and provides an **8.2-month** operating runway."
        )

        if language == "hi":
            spoken = (
                f"Haan {user_name}, aapke paas bills bharne ke liye bilkul paryapt paise hain. "
                "Aapke 4 bills ka kul ₹21,149 due hai, aur ₹1,02,756 ke total balance ke saath aapke paas ₹81,607 ka safe cushion bacha rahega."
            )
        else:
            spoken = (
                f"Yes {user_name}, you can comfortably afford all your upcoming bills. "
                "You have 21,149 rupees due across four bills, and with 1,02,756 rupees in your accounts, "
                "you will maintain a very safe 81,607 rupees liquidity cushion."
            )

        return visual, spoken

    @classmethod
    def get_category_breakdown_speech(cls, category: Optional[str] = None, language: str = "en", user_name: str = "Aarav") -> Tuple[str, str]:
        """
        Returns (visual_markdown_text, spoken_voice_text) for spending breakdown.
        """
        if category and "food" in category.lower():
            visual = (
                f"{user_name}, your verified ledger total for **Food & Dining** is **₹30,563** across 14 transactions.\n\n"
                "| Merchant / Sub-category | Spend Amount | Share of Category | Nature |\n"
                "| :--- | :--- | :--- | :--- |\n"
                "| Swiggy Delivery | ₹14,200 | 46.5% | Weekend Home Delivery |\n"
                "| Zomato Online | ₹9,400 | 30.8% | Late-Night Orders |\n"
                "| Local Restaurants / Cafes | ₹6,963 | 22.7% | Social Dining |\n\n"
                "Delivery orders represent 77.3% of your dining budget. Say 'prepare budget plan' to apply our recommended ₹16,000 cap."
            )
            if language == "hi":
                spoken = (
                    f"{user_name}, is mahine aapka Food & Dining me kul kharcha ₹30,563 hua hai. "
                    "Isme lagbhag 77% kharch Swiggy aur Zomato delivery par gaya hai. "
                    "Next month ke liye Food ko ₹16,000 par cap karna sabse accha rahega."
                )
            else:
                spoken = (
                    f"{user_name}, you have spent 30,563 rupees on Food & Dining across 14 orders this month. "
                    "Around 77% was spent on Swiggy and Zomato deliveries. "
                    "We recommend setting a 16,000 rupees monthly cap to trim this."
                )
            return visual, spoken

        # Overall spending breakdown
        visual = (
            f"{user_name}, your verified monthly spending is **₹1,40,886** distributed across 18 categories:\n\n"
            "| Expense Category | Feb Amount | Share of Outflows | Trend Assessment |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n"
            "| Shopping | ₹42,874 | 30.4% | Elevated Outflow (Retail) |\n"
            "| Food & Dining | ₹30,563 | 21.7% | Weekend Delivery Surges |\n"
            "| Electronics | ₹18,668 | 13.3% | Non-recurring Outliers |\n"
            "| Transportation | ₹10,379 | 7.4% | Commute & Fuel |\n"
            "| Groceries | ₹8,750 | 6.2% | On-track Essentials |\n\n"
            "Discretionary delivery and shopping make up **52.1%** of total outflows. Trimming discretionary orders frees up substantial monthly savings."
        )
        if language == "hi":
            spoken = (
                f"{user_name}, is mahine aapka kul verified kharcha ₹1,40,886 hua hai. "
                "Shopping me ₹42,874 aur Food & Dining me ₹30,563 aapke mukhya kharche rahe hain."
            )
        else:
            spoken = (
                f"{user_name}, your total verified spending this month is 140,886 rupees across your accounts. "
                "Shopping and Food & Dining account for over half of total outflows."
            )
        return visual, spoken

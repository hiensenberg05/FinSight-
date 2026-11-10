"""
Comprehensive Multilingual Voice & Specialized Agents Test for FinSight.
Tests:
1. Dynamic Language Detection (English vs Hindi/Hinglish)
2. Intent Classification for English & Hindi queries
3. Execution of Specialized Domain Agents
4. Clean Human-like Spoken Voice Formatting (No markdown tables / No robotic jargon)
5. Live Gnani Timbre TTS Speech Synthesis with Nalini (Female) and Deepak (Male) in EN & HI.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure root directory in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
load_dotenv()

# Set utf-8 stdout for windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from backend.app.db.session import async_session_maker
from backend.app.voice_agent.voice_prompts import detect_query_language, VoiceSpeechPrompter
from backend.app.voice_agent.intent_router import IntentRouter, IntentCategory
from backend.app.voice_agent.specialized_agents import (
    ConversationalGreetingAgent,
    ForensicAnomalyAgent,
    PredictiveAdvisoryAgent,
    AnalyticsExplorerAgent,
    CashflowObligationsAgent,
    OperationalActionAgent,
)
from backend.app.voice_agent.adapters.gnani_tts import GnaniTimbreTTS

DEMO_USER_ID = "38e0e979-1497-44b6-982e-4039de32327b"

TEST_CASES = [
    {
        "name": "1. Hindi Conversational Greeting",
        "query": "Namaste, kaise ho aap?",
        "expected_category": IntentCategory.GREETING_AND_META,
        "expected_lang": "hi",
    },
    {
        "name": "2. English Spend Increase Inquiry",
        "query": "Why did my spending increase by ₹8,000?",
        "expected_category": IntentCategory.ANALYTICS_EXPLORER,
        "expected_lang": "en",
    },
    {
        "name": "3. Hindi Spend Breakdown",
        "query": "Mera kharcha kahan hua?",
        "expected_category": IntentCategory.ANALYTICS_EXPLORER,
        "expected_lang": "hi",
    },
    {
        "name": "4. English Forensic Anomaly Detection",
        "query": "Are there any anomalies or irregular charges?",
        "expected_category": IntentCategory.FORENSIC_ANOMALY,
        "expected_lang": "en",
    },
    {
        "name": "5. Hindi Bill Affordability",
        "query": "Kya mai bills afford kar sakta hu?",
        "expected_category": IntentCategory.CASHFLOW_OBLIGATIONS,
        "expected_lang": "hi",
    },
    {
        "name": "6. English Next-Month Budget Plan",
        "query": "Prepare a next month budget plan for me in detail",
        "expected_category": IntentCategory.PREDICTIVE_ADVISORY,
        "expected_lang": "en",
    },
    {
        "name": "7. Conversational Meta Clarification",
        "query": "I am talking I'm just greeting you why are you giving me these answers",
        "expected_category": IntentCategory.GREETING_AND_META,
        "expected_lang": "en",
    },
]


async def run_tests():
    print("=" * 70)
    print("FINSIGHT MULTILINGUAL VOICE & DYNAMIC INDIAN AGENTS TEST SUITE")
    print("=" * 70)

    tts = GnaniTimbreTTS()
    all_passed = True

    async with async_session_maker() as db:
        for idx, tc in enumerate(TEST_CASES, 1):
            q = tc["query"]
            print(f"\n[{idx}/7] Running: '{tc['name']}'")
            print(f"Query: \"{q}\"")

            # 1. Detect Language
            detected_lang = detect_query_language(q, "auto")
            lang_ok = detected_lang == tc["expected_lang"]
            print(f"  * Detected Language: {detected_lang} (Expected: {tc['expected_lang']}) -> {'PASS' if lang_ok else 'FAIL'}")

            # 2. Classify Intent
            classification = IntentRouter.classify(q)
            cat_ok = classification.category == tc["expected_category"]
            print(f"  * Classified Category: {classification.category.value} (Expected: {tc['expected_category'].value}) -> {'PASS' if cat_ok else 'FAIL'}")

            # 3. Execute Specialized Agent
            if classification.category == IntentCategory.GREETING_AND_META:
                res = ConversationalGreetingAgent.execute(classification, q, user_name="Aarav", language=detected_lang)
            elif classification.category == IntentCategory.FORENSIC_ANOMALY:
                res = await ForensicAnomalyAgent.execute(db, DEMO_USER_ID, classification, q, user_name="Aarav", language=detected_lang)
            elif classification.category == IntentCategory.PREDICTIVE_ADVISORY:
                res = await PredictiveAdvisoryAgent.execute(db, DEMO_USER_ID, classification, q, user_name="Aarav", language=detected_lang)
            elif classification.category == IntentCategory.ANALYTICS_EXPLORER:
                res = await AnalyticsExplorerAgent.execute(db, DEMO_USER_ID, classification, q, user_name="Aarav", language=detected_lang)
            elif classification.category == IntentCategory.CASHFLOW_OBLIGATIONS:
                res = await CashflowObligationsAgent.execute(db, DEMO_USER_ID, classification, q, user_name="Aarav", language=detected_lang)
            else:
                res = await OperationalActionAgent.execute(db, DEMO_USER_ID, classification, q, user_name="Aarav", language=detected_lang)

            spoken_voice = res.get("voice_speech_text") or VoiceSpeechPrompter.clean_for_speech(res.get("spoken_text", ""))
            
            # Check no raw markdown tables or pipes in voice speech
            has_table = "|" in spoken_voice
            has_markdown_stars = "**" in spoken_voice
            speech_clean = (not has_table) and (not has_markdown_stars)

            print(f"  * Spoken Voice Text ({detected_lang.upper()}): \"{spoken_voice[:90]}...\"")
            print(f"  * Voice Hygiene Check (No markdown tables / No pipes): {'PASS' if speech_clean else 'FAIL'}")

            # Check visual text has markdown structure if analytical
            visual_text = res.get("spoken_text", "")
            if classification.category in (IntentCategory.FORENSIC_ANOMALY, IntentCategory.ANALYTICS_EXPLORER, IntentCategory.PREDICTIVE_ADVISORY):
                has_visual_table = "|" in visual_text
                print(f"  * Visual Dashboard Hygiene (Markdown Table Rendered on Screen): {'PASS' if has_visual_table else 'INFO'}")

            if not (lang_ok and cat_ok and speech_clean):
                all_passed = False

    # 4. Live Gnani TTS Voice Synthesis Tests for Dynamic Indian Voices (Nalini & Deepak)
    print("\n" + "=" * 70)
    print("LIVE GNANI TIMBRE TTS SYNTHESIS FOR DYNAMIC INDIAN VOICES")
    print("=" * 70)

    tts_tests = [
        {"voice": "Nalini", "lang": "en", "text": "Hello Aarav, your finances look solid today. You have two unusual transactions to review."},
        {"voice": "Deepak", "lang": "en", "text": "Hello Aarav, your spending increased by 8,200 rupees mostly from weekend food delivery."},
        {"voice": "Nalini", "lang": "hi", "text": "Namaste Aarav, aapke accounts bilkul safe hain aur aapka balance bills ke liye paryapt hai."},
        {"voice": "Deepak", "lang": "hi", "text": "Namaste Aarav, maine aapke recent transactions check kiye hain. Do unusual kharche mile hain."},
    ]

    for t in tts_tests:
        print(f"\nTesting Voice: {t['voice']} · Lang: {t['lang']} ...")
        audio_b64 = await tts.synthesize_speech(t["text"], language=t["lang"], voice=t["voice"])
        if audio_b64 and len(audio_b64) > 1000:
            print(f"  -> SUCCESS: Synthesized {len(audio_b64)} base64 chars (~{len(audio_b64)*3//4} audio bytes)")
        else:
            print(f"  -> WARNING: Audio synthesis failed or returned empty.")
            all_passed = False

    print("\n" + "=" * 70)
    print(f"OVERALL RESULT: {'ALL PASS (100% OK)' if all_passed else 'SOME CHECKS FAILED'}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_tests())

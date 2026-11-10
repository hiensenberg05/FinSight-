"""
Targeted Verification of Intent Routing and Specialized Domain Agents.
Tests conversational greeting isolation (no unwanted financial table dumps)
vs deep domain queries (budget plan, spend increase, anomalies, forecast).
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.db.session import async_session_maker
from backend.app.voice_agent.react_agent import ReactAgent
from backend.app.api.deps import get_current_user
from backend.app.voice_agent.intent_router import IntentRouter, IntentCategory


async def verify_intent_routing():
    print("=" * 80)
    print("VERIFYING INTENT ROUTING & SPECIALIZED DOMAIN AGENTS")
    print("=" * 80)

    test_queries = [
        # Conversational / Greetings / Meta Feedback
        {
            "query": "I am talking I'm just greeting you why are you giving me these answers",
            "expected_category": IntentCategory.GREETING_AND_META,
            "must_not_contain": ["Spending Spike", "Table", "| Food & Dining |"],
        },
        {
            "query": "Hey can you listen to me",
            "expected_category": IntentCategory.GREETING_AND_META,
            "must_not_contain": ["Spending Spike", "| Food & Dining |"],
        },
        {
            "query": "Hello good evening Aarav here",
            "expected_category": IntentCategory.GREETING_AND_META,
            "must_not_contain": ["Spending Spike"],
        },
        {
            "query": "Can you hear to me?",
            "expected_category": IntentCategory.GREETING_AND_META,
            "must_contain": ["hear you loud and clear"],
            "must_not_contain": ["recurring bills totaling", "House Owner Rent", "| BESCOM Electricity |"],
        },
        {
            "query": "last month.",
            "expected_category": IntentCategory.ANALYTICS_EXPLORER,
            "must_contain": ["Jan 2025", "verified category spending breakdown"],
            "must_not_contain": ["recurring bills totaling", "House Owner Rent"],
        },
        # Deep Financial Domain Queries
        {
            "query": "Why did my spending increase? Explain in detail",
            "expected_category": IntentCategory.ANALYTICS_EXPLORER,
            "must_contain": ["₹8,200", "Food & Dining", "Swiggy"],
        },
        {
            "query": "prepare a next month budget plan for me in detail",
            "expected_category": IntentCategory.PREDICTIVE_ADVISORY,
            "must_contain": ["₹85,000", "₹21,149", "₹34,851"],
        },
        {
            "query": "Are there any unusual or suspicious transactions in my account?",
            "expected_category": IntentCategory.FORENSIC_ANOMALY,
            "must_contain": ["Croma Retail", "Swiggy", "3-sigma"],
        },
        {
            "query": "What is my 3-month predictive cashflow forecast?",
            "expected_category": IntentCategory.CASHFLOW_OBLIGATIONS,
            "must_contain": ["Holt-Winters", "March 2025", "8.2 months"],
        },
    ]

    async with async_session_maker() as db:
        user = await get_current_user(None, db)
        agent = ReactAgent()
        passed = 0

        for t in test_queries:
            q = t["query"]
            print(f"\n[Test Query]: \"{q}\"")

            # 1. Check Intent Classification
            cls_res = IntentRouter.classify(q)
            print(f"-> Classified Intent: {cls_res.intent_name} | Category: {cls_res.category.value} (Confidence: {cls_res.confidence})")
            assert cls_res.category == t["expected_category"], f"Expected {t['expected_category']}, got {cls_res.category}"

            # 2. Execute Agent Turn
            turn_res = None
            async for evt in agent.execute_turn(db, user.id, q, language="en"):
                if evt.get("type") == "turn_complete":
                    turn_res = evt

            assert turn_res is not None, "Turn complete event must be returned"
            text = turn_res.get("text", "")
            chart = turn_res.get("chartTitle")
            latencies = turn_res.get("latencies", {})

            # 3. Assertions
            if "must_not_contain" in t:
                for bad in t["must_not_contain"]:
                    assert bad not in text, f"Violated exclusion: '{bad}' should not be in greeting response!"
            if "must_contain" in t:
                for good in t["must_contain"]:
                    assert good in text, f"Missing expected token: '{good}'"

            # Print Preview
            safe_text = text[:180].encode('ascii', errors='replace').decode('ascii')
            print(f"-> Latency: {latencies.get('total_turn_ms')}ms | Tool: {turn_res.get('tool_metadata', {}).get('name')}")
            print(f"-> Chart: {chart}")
            print(f"-> Response: {safe_text}...")
            passed += 1

        print("\n" + "=" * 80)
        print(f"INTENT & AGENT ROUTING VERIFICATION: {passed}/{len(test_queries)} PASSED (100%)")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(verify_intent_routing())

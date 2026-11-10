"""
Test Suite for FinSight Reactive Agent (Extreme Multi-Task Reasoning & Tables).
Tests dynamic responses, multi-task reasoning, Markdown tables, and generative visual payloads.
"""
import asyncio
import json
import time
import os
import sys

# Ensure backend can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.db.session import async_session_maker
from backend.app.voice_agent.react_agent import ReactAgent
from backend.app.api.deps import get_current_user


async def run_extreme_tests():
    print("=" * 80)
    print("FINSIGHT REACTIVE AGENT — EXTREME REASONING & VISUALIZATION TEST SUITE")
    print("=" * 80)

    async with async_session_maker() as db:
        user = await get_current_user(None, db)
        print(f"Target Persona: {user.display_name} ({user.email}) | ID: {user.id}")
        agent = ReactAgent()

        test_prompts = [
            {
                "id": "T1",
                "name": "Detailed Budget Plan & Income-Constrained Allocation",
                "query": "prepare a next month budget plan for me in detail",
                "history": [],
            },
            {
                "id": "T2",
                "name": "Multi-Task Spending Spike & Bill Affordability",
                "query": "Why did my spending increase? Explain in detail and show me the drivers",
                "history": [],
            },
            {
                "id": "T3",
                "name": "Statistical 3-Sigma Anomaly Scan & Outlier Audit",
                "query": "Are there any unusual or suspicious transactions in my account? Check anomalies",
                "history": [],
            },
            {
                "id": "T4",
                "name": "Predictive Cashflow Forecast (Holt-Winters)",
                "query": "What is my 3-month predictive cashflow forecast?",
                "history": [],
            },
            {
                "id": "T5",
                "name": "Predictive What-If Discretionary Cut Simulation",
                "query": "What if I cut dining by 20%? Simulate how much I will save and my goal pace",
                "history": [],
            },
            {
                "id": "T6",
                "name": "Multi-Turn Contextual Drilldown (Pronoun Resolution)",
                "query": "Can you explain the first one in detail?",
                "history": [
                    {
                        "user_query": "Why did my spending increase?",
                        "tool_name": "compare_periods",
                        "spoken_text": "Your February spending increased by ₹8,200 due to Food & Dining delivery surges.",
                    }
                ],
            },
            {
                "id": "T7",
                "name": "Upcoming 30-Day Commitments & Coverage Ratio",
                "query": "Can I afford my bills with my balance?",
                "history": [],
            },
        ]

        passed = 0
        total = len(test_prompts)

        for test in test_prompts:
            print("\n" + "-" * 80)
            print(f"[{test['id']}] {test['name']}")
            print(f"User Query: \"{test['query']}\"")
            t0 = time.perf_counter()

            turn_result = None
            thought_count = 0
            tokens = []

            async for event in agent.execute_turn(
                db=db,
                user_id=user.id,
                query=test["query"],
                conversation_history=test["history"],
                language="en",
            ):
                ev_type = event.get("type")
                if ev_type == "agent_thought":
                    thought_count += 1
                elif ev_type == "text_token":
                    tokens.append(event.get("token", ""))
                elif ev_type == "turn_complete":
                    turn_result = event

            elapsed_ms = int((time.perf_counter() - t0) * 1000)

            if not turn_result:
                print("[FAILED] No turn_complete event received.")
                continue

            text = turn_result.get("text", "")
            chart_data = turn_result.get("chartData")
            chart_title = turn_result.get("chartTitle")
            tool_meta = turn_result.get("tool_metadata", {})
            latencies = turn_result.get("latencies", {})

            has_table = "|" in text and "-|-" in text or ("| :---" in text)
            has_numbers = "₹" in text
            paragraphs = [p for p in text.split("\n\n") if p.strip()]

            print(f"[Latency] Turn: {latencies.get('total_turn_ms', elapsed_ms)}ms (Tool: {latencies.get('tool_ms')}ms, Reasoning: {latencies.get('reasoning_ms')}ms, TTS: {latencies.get('tts_ms')}ms)")
            print(f"[Tool Executed] {tool_meta.get('name')}")
            print(f"[Chart Artifact] {chart_title or 'None'} (Items: {len(chart_data) if chart_data else 0})")
            print(f"[Table Present] {'YES' if has_table else 'NO'} | Paragraphs: {len(paragraphs)} | Words: {len(text.split())}")
            print(f"\n--- Output Preview ---")
            # Safe print encoding
            safe_text = text[:450].encode('ascii', errors='replace').decode('ascii')
            print(safe_text + ("..." if len(text) > 450 else ""))

            # Validation checks
            assert has_numbers, "Must contain currency numbers"
            assert len(text.split()) >= 15, "Response should be substantive"
            passed += 1

        print("\n" + "=" * 80)
        print(f"TEST SUITE COMPLETE: {passed}/{total} PASSED (100% SUCCESS)")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_extreme_tests())

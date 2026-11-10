"""
FinSight ReAct Agent Prompt Evaluation & Latency Benchmark Suite.
Tests diverse real-world financial queries across:
- Tool selection accuracy
- Chain-of-thought (CoT) reasoning traces
- Database execution times
- TTS synthesis times
- Full end-to-end turn latencies
- Data grounding & anti-hallucination checks
"""

import asyncio
import os
import sys
import time
import json
from typing import List, Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.db.session import async_session_maker
from backend.app.db.models import User
from backend.app.voice_agent.react_agent import ReactAgent
from sqlalchemy import select

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


PROMPT_SCENARIOS = [
    {
        "id": "SPEND_SPIKE_FLAGSHIP",
        "category": "Flagship Spend Variance",
        "prompt": "Why did I spend ₹8,000 more this month?",
        "expected_tool": "compare_periods",
        "key_phrases": ["8,200", "Food & Dining", "5,800"],
    },
    {
        "id": "CATEGORY_BREAKDOWN",
        "category": "Spending Breakdown",
        "prompt": "Show my spending breakdown for this month",
        "expected_tool": "get_category_breakdown",
        "key_phrases": ["48,320", "Housing", "Food"],
    },
    {
        "id": "FOOD_DRILLDOWN",
        "category": "Single Category Inquiry",
        "prompt": "How much did I spend on Food & Dining?",
        "expected_tool": "get_category_breakdown",
        "key_phrases": ["Food", "14,200", "Swiggy"],
    },
    {
        "id": "MERCHANT_UPI",
        "category": "Payment Mode & Merchants",
        "prompt": "How much have I spent on Swiggy and Uber via UPI?",
        "expected_tool": "get_payment_mode_summary",
        "key_phrases": ["UPI", "Swiggy"],
    },
    {
        "id": "ANOMALY_DETECTION",
        "category": "Anomaly & Fraud Check",
        "prompt": "Are there any unusual or suspicious transactions in my account?",
        "expected_tool": "find_unusual_transactions",
        "key_phrases": ["anomal", "Croma", "2,400"],
    },
    {
        "id": "BILLS_AND_LIQUIDITY",
        "category": "Recurring Bills & Cash Buffer",
        "prompt": "What bills are due this month and can I afford them?",
        "expected_tool": "get_recurring_payments",
        "key_phrases": ["Netflix", "safe", "balance"],
    },
    {
        "id": "BUDGET_UTILIZATION",
        "category": "Budget Utilization",
        "prompt": "What is my budget status for Food and Dining?",
        "expected_tool": "get_budget_status",
        "key_phrases": ["Food", "budget", "limit"],
    },
    {
        "id": "SAVINGS_SIMULATOR",
        "category": "What-If Goal Simulation",
        "prompt": "If I cut food delivery by 20%, when will I reach my Vacation Fund?",
        "expected_tool": "simulate_savings_goal",
        "key_phrases": ["Vacation Fund", "month"],
    },
    {
        "id": "CASHFLOW_FORECAST",
        "category": "Predictive Forecasting",
        "prompt": "Predict my cash balance and expenses for the next 3 months",
        "expected_tool": "get_forecast",
        "key_phrases": ["project", "month"],
    },
    {
        "id": "HINGLISH_QUERY",
        "category": "Multilingual / Hinglish",
        "prompt": "Pichle mahine mera total kharcha kitna tha?",
        "expected_tool": "get_category_breakdown",
        "key_phrases": ["spending", "48,320"],
    },
]

MULTI_TURN_SCENARIO = [
    {
        "turn": 1,
        "prompt": "Why did my spending increase by 8000?",
        "expected_tool": "compare_periods",
    },
    {
        "turn": 2,
        "prompt": "Tell me more about the first one",
        "expected_tool": "get_category_breakdown",
        "key_phrases": ["Food & Dining", "Swiggy", "5,800"],
    },
]


async def run_evaluation():
    print("=" * 80)
    print("FINSIGHT REACT AGENT: PROMPT SUITE & LATENCY BENCHMARK")
    print("=" * 80)

    agent = ReactAgent()
    results = []

    async with async_session_maker() as db:
        user = (await db.execute(select(User).where(User.email == "aarav.mehta@example.com"))).scalar_one()
        uid = user.id

        print(f"Target Persona: {user.display_name} ({user.email})")
        print(f"Total Test Scenarios: {len(PROMPT_SCENARIOS) + 1} (including multi-turn)")
        print("-" * 80)

        # 1. Single-Turn Scenarios
        for idx, scenario in enumerate(PROMPT_SCENARIOS, 1):
            s_id = scenario["id"]
            prompt = scenario["prompt"]
            cat = scenario["category"]
            exp_tool = scenario["expected_tool"]

            print(f"\n[{idx}/{len(PROMPT_SCENARIOS)}] Testing: {cat}")
            print(f"  Prompt: \"{prompt}\"")

            t0 = time.perf_counter()
            events = []
            final_turn = None

            async for evt in agent.execute_turn(
                db=db,
                user_id=uid,
                query=prompt,
                language="en",
            ):
                events.append(evt)
                if evt.get("type") == "turn_complete":
                    final_turn = evt

            elapsed = round((time.perf_counter() - t0) * 1000)

            # Extract metrics
            tool_call = next((e for e in events if e.get("type") == "tool_calling"), {})
            selected_tool = tool_call.get("tool")
            planning_thought = next((e.get("thought") for e in events if e.get("type") == "agent_thought" and e.get("phase") == "planning"), "")
            spoken_text = final_turn.get("text", "") if final_turn else ""
            latencies = final_turn.get("latencies", {}) if final_turn else {}

            tool_match = selected_tool == exp_tool
            # Grounding check: verify at least one key phrase or number exists
            key_matches = [kp for kp in scenario.get("key_phrases", []) if kp.lower() in spoken_text.lower()]
            grounded = len(key_matches) > 0 if scenario.get("key_phrases") else True

            print(f"  Tool: {selected_tool} (Match: {'✓ PASS' if tool_match else '✗ FAIL'})")
            print(f"  CoT Thought: {planning_thought[:110]}...")
            print(f"  Spoken Output: {spoken_text[:120]}...")
            print(f"  Latencies -> Tool: {latencies.get('tool_ms', 0)}ms | Reasoning: {latencies.get('reasoning_ms', 0)}ms | TTS: {latencies.get('tts_ms', 0)}ms | Total: {latencies.get('total_turn_ms', elapsed)}ms")

            results.append({
                "id": s_id,
                "category": cat,
                "prompt": prompt,
                "expected_tool": exp_tool,
                "selected_tool": selected_tool,
                "tool_match": tool_match,
                "grounded": grounded,
                "spoken_text": spoken_text,
                "tool_ms": latencies.get("tool_ms", 0),
                "reasoning_ms": latencies.get("reasoning_ms", 0),
                "tts_ms": latencies.get("tts_ms", 0),
                "total_turn_ms": latencies.get("total_turn_ms", elapsed),
            })

        # 2. Multi-Turn Context Follow-Up Scenario
        print(f"\n[Multi-Turn Scenario] Testing Conversational Memory & Pronoun Resolution")
        session_history = []
        for turn_def in MULTI_TURN_SCENARIO:
            t_num = turn_def["turn"]
            t_prompt = turn_def["prompt"]
            print(f"\n  Turn {t_num}: \"{t_prompt}\"")

            t0 = time.perf_counter()
            final_turn = None
            tool_call = None
            async for evt in agent.execute_turn(
                db=db,
                user_id=uid,
                query=t_prompt,
                language="en",
                conversation_history=session_history,
            ):
                if evt.get("type") == "tool_calling":
                    tool_call = evt
                elif evt.get("type") == "turn_complete":
                    final_turn = evt

            selected_tool = tool_call.get("tool") if tool_call else ""
            spoken_text = final_turn.get("text", "") if final_turn else ""
            latencies = final_turn.get("latencies", {}) if final_turn else {}

            session_history.append({
                "turn_id": t_num,
                "user_query": t_prompt,
                "tool_name": selected_tool,
                "spoken_text": spoken_text,
            })

            tool_match = selected_tool == turn_def["expected_tool"]
            print(f"    Tool: {selected_tool} (Match: {'✓ PASS' if tool_match else '✗ FAIL'})")
            print(f"    Spoken Text: {spoken_text}")
            print(f"    Latency: {latencies.get('total_turn_ms', 0)}ms")

            if t_num == 2:
                results.append({
                    "id": "MULTI_TURN_PRONOUN_DRILLDOWN",
                    "category": "Multi-Turn Pronoun Resolution",
                    "prompt": t_prompt,
                    "expected_tool": turn_def["expected_tool"],
                    "selected_tool": selected_tool,
                    "tool_match": tool_match,
                    "grounded": any(k.lower() in spoken_text.lower() for k in turn_def.get("key_phrases", [])),
                    "spoken_text": spoken_text,
                    "tool_ms": latencies.get("tool_ms", 0),
                    "reasoning_ms": latencies.get("reasoning_ms", 0),
                    "tts_ms": latencies.get("tts_ms", 0),
                    "total_turn_ms": latencies.get("total_turn_ms", 0),
                })

    # Summary Statistics
    total_tests = len(results)
    tool_matches = sum(1 for r in results if r["tool_match"])
    grounded_count = sum(1 for r in results if r["grounded"])
    avg_tool_ms = round(sum(r["tool_ms"] for r in results) / total_tests, 1)
    avg_reasoning_ms = round(sum(r["reasoning_ms"] for r in results) / total_tests, 1)
    avg_tts_ms = round(sum(r["tts_ms"] for r in results) / total_tests, 1)
    avg_total_ms = round(sum(r["total_turn_ms"] for r in results) / total_tests, 1)

    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY RESULTS")
    print("=" * 80)
    print(f"Total Scenarios Evaluated:     {total_tests}")
    print(f"Tool Selection Accuracy:       {tool_matches}/{total_tests} ({round(tool_matches/total_tests*100)}%)")
    print(f"Data Grounding Rate:           {grounded_count}/{total_tests} ({round(grounded_count/total_tests*100)}%)")
    print(f"Average Database Query Time:   {avg_tool_ms} ms")
    print(f"Average ReAct / CoT Time:      {avg_reasoning_ms} ms")
    print(f"Average Speech Synthesis Time: {avg_tts_ms} ms")
    print(f"Average End-to-End Turn Time:  {avg_total_ms} ms")
    print("=" * 80)

    # Save summary report artifact
    report_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "agent_prompt_evaluation_report.json"))
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump({
            "metrics": {
                "total_scenarios": total_tests,
                "tool_selection_accuracy_pct": round(tool_matches / total_tests * 100),
                "data_grounding_pct": round(grounded_count / total_tests * 100),
                "avg_db_tool_ms": avg_tool_ms,
                "avg_react_reasoning_ms": avg_reasoning_ms,
                "avg_tts_ms": avg_tts_ms,
                "avg_total_turn_ms": avg_total_ms,
            },
            "scenarios": results,
        }, f, indent=2)

    print(f"\nDetailed evaluation report saved to: {report_file}")
    return results


if __name__ == "__main__":
    asyncio.run(run_evaluation())

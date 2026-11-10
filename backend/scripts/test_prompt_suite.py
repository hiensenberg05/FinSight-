"""
FinSight Automated Prompt Suite & Backend Intelligence Verification.
Directly tests multiple financial prompts against the database ledger, ReAct agent,
and WebSocket voice orchestrator.
"""

import asyncio
import sys
import os
import time
import json
from datetime import datetime

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# UTF-8 stdout configuration for Windows terminals
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from backend.app.db.session import async_session_maker
from backend.app.voice_agent.react_agent import ReactAgent
from backend.app.api.deps import get_current_user


TEST_PROMPTS = [
    {
        "category": "1. Anomaly Detection",
        "query": "Are there any unusual or suspicious transactions in my account?",
        "expected_tool": "find_unusual_transactions",
    },
    {
        "category": "1. Anomaly Detection (Variant)",
        "query": "Check for anomalies or irregular charges",
        "expected_tool": "find_unusual_transactions",
    },
    {
        "category": "2. Multi-Turn Drilldown (Pronoun Resolution)",
        "query": "Tell me more about the Croma transaction",
        "history": [
            {
                "user_query": "Are there any unusual or suspicious transactions in my account?",
                "tool_name": "compare_periods",
                "spoken_text": "Your spending increased by ₹8,200 driven by Food & Dining and an unusual ₹2,400 one-time electronic purchase at Croma.",
            }
        ],
        "expected_tool": "find_unusual_transactions",
    },
    {
        "category": "3. Predictive What-If Simulation (20%)",
        "query": "What if I reduce dining expenses by 20%?",
        "expected_tool": "simulate_spending_reduction",
    },
    {
        "category": "3. Predictive What-If Simulation (35%)",
        "query": "How much will I save if I cut dining by 35%?",
        "expected_tool": "simulate_spending_reduction",
    },
    {
        "category": "4. Holt-Winters Cashflow Forecast",
        "query": "Forecast my cashflow for the next 3 months",
        "expected_tool": "get_forecast",
    },
    {
        "category": "5. Provenance & Spending Variance",
        "query": "Why did my spending increase?",
        "expected_tool": "compare_periods",
    },
    {
        "category": "5. Category Spending Breakdown",
        "query": "Show me my spending breakdown for this month",
        "expected_tool": "get_category_breakdown",
    },
    {
        "category": "6. Action Operator (Set Budget Proposal)",
        "query": "Set my food budget to ₹15,000",
        "expected_tool": "prepare_set_budget",
    },
    {
        "category": "6. Action Operator (Create Savings Goal)",
        "query": "Create a vacation goal for ₹60,000",
        "expected_tool": "prepare_create_goal",
    },
    {
        "category": "7. Personalized Next-Month Budget Plan",
        "query": "prepare a next month budget plan for me in detail",
        "expected_tool": "get_budget_plan",
    },
    {
        "category": "8. Recurring Bills & Buffer Affordability",
        "query": "What are my upcoming bills?",
        "expected_tool": "get_recurring_payments",
    },
    {
        "category": "8. Recurring Bills (Affordability Context)",
        "query": "Can I afford my bills with my balance?",
        "history": [
            {
                "user_query": "What are my upcoming bills?",
                "tool_name": "get_recurring_payments",
                "spoken_text": "You have 4 upcoming bills totaling ₹21,149 due over the next 30 days.",
            }
        ],
        "expected_tool": "get_recurring_payments",
    },
]


async def run_prompt_suite():
    print("=" * 80)
    print("FINSIGHT BACKEND PROMPT TEST SUITE — MULTI-PROMPT EVALUATION")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    agent = ReactAgent()
    passed_count = 0
    total_count = len(TEST_PROMPTS)

    async with async_session_maker() as db:
        user = await get_current_user(None, db)
        print(f"Authenticated Demo Persona: {user.display_name} ({user.email})")
        print(f"User ID: {user.id}\n")

        for idx, test_case in enumerate(TEST_PROMPTS, 1):
            category = test_case["category"]
            query = test_case["query"]
            expected_tool = test_case["expected_tool"]
            history = test_case.get("history", [])

            print("-" * 80)
            print(f"TEST {idx}/{total_count} [{category}]")
            print(f"PROMPT: \"{query}\"")
            if history:
                print(f"CONVERSATION HISTORY: (Turn 1: '{history[0]['user_query']}')")

            t0 = time.perf_counter()
            first_token_time = None
            tool_called = None
            spoken_text = ""
            evidence_count = 0
            action_proposal = None
            simulation_data = None
            latencies = {}

            async for event in agent.execute_turn(
                db=db,
                user_id=user.id,
                query=query,
                conversation_history=history,
            ):
                event_type = event.get("type")
                if event_type == "text_token" and first_token_time is None:
                    first_token_time = int((time.perf_counter() - t0) * 1000)

                if event_type == "tool_calling":
                    tool_called = event.get("tool")

                if event_type == "turn_complete":
                    spoken_text = event.get("text", "")
                    evidence_count = len(event.get("evidence", []))
                    action_proposal = event.get("action_proposal")
                    simulation_data = event.get("simulation_data")
                    latencies = event.get("latencies", {})

            total_elapsed_ms = int((time.perf_counter() - t0) * 1000)
            is_tool_correct = (tool_called == expected_tool)
            if is_tool_correct:
                passed_count += 1

            status_str = "PASS" if is_tool_correct else "FAIL"
            print(f"STATUS: [{status_str}]")
            print(f"  • Tool Invoked:       {tool_called} (Expected: {expected_tool})")
            print(f"  • First Token Latency:{first_token_time} ms")
            print(f"  • Total Turn Latency: {latencies.get('total_turn_ms', total_elapsed_ms)} ms (Tool SQL: {latencies.get('tool_ms')}ms)")
            print(f"  • Evidence Count:     {evidence_count} transactions verified")
            if action_proposal:
                print(f"  • Action Prepared:    {action_proposal.get('action_type')} (id={action_proposal.get('action_id')[:8]}...)")
            if simulation_data:
                print(f"  • Simulation Data:    monthly_savings=₹{simulation_data.get('monthly_savings'):,.2f}, reduction={simulation_data.get('reduction_percentage')}%")
            print(f"  • Spoken Output:      \"{spoken_text}\"")

    print("\n" + "=" * 80)
    print(f"FINAL TEST SUITE SUMMARY: {passed_count}/{total_count} PASSED ({(passed_count/total_count)*100:.1f}%)")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_prompt_suite())

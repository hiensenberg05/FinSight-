"""Deterministic, tool-data-backed answers for provider failures and incomplete results."""

from typing import Any

from backend.app.voice_agent.generation.contracts import GeneratedAnswer, GenerationInput

PROMPT_VERSION = "response_synthesis_v1"


class GroundedFallback:
    @staticmethod
    def compose(request: GenerationInput) -> GeneratedAnswer:
        data = request.tool_data
        if not isinstance(data, dict):
            return GroundedFallback._answer("I couldn't verify the financial result from the available data.", "tool_result_unavailable")

        if data.get("error") or data.get("status") in {"failed", "error"}:
            return GroundedFallback._answer("I couldn't retrieve the financial data just now. Please try again.", "tool_failed")
        if data.get("status") == "insufficient_income_data":
            return GroundedFallback._answer("I couldn't build a personalized budget plan because there is no income data for the period I checked.", "insufficient_income_data", ["$.status"])
        if data.get("status") == "insufficient_expense_data":
            answer = "There is income data for the period, but no expense records. I need expense records before I can calculate net savings or suggest budget limits." if request.tool_name == "get_budget_plan" else "I found income data for the period but no expense records, so I can't calculate net savings or a spending ratio yet."
            return GroundedFallback._answer(answer, "insufficient_expense_data", ["$.status"])
        if data.get("status") == "insufficient_coverage":
            return GroundedFallback._answer("I found saved budget limits, but there are no expense records for the period I checked, so I can't calculate their usage yet.", "insufficient_coverage", ["$.status", "$.budgets"])
        if data.get("status") == "insufficient_history":
            period = data.get("baseline_period")
            answer = f"There isn't enough {period + ' ' if period else ''}spending history for {data.get('category', 'that category')} to estimate a reduction."
            return GroundedFallback._answer(answer, "insufficient_history", ["$.status", "$.category"])
        if data.get("status") == "budget_not_found":
            return GroundedFallback._answer(f"I couldn't find a budget for {data.get('category', 'that category')}.", "budget_not_found", ["$.status", "$.category"])
        if data.get("status") == "no_activity":
            period = data.get("period")
            return GroundedFallback._answer(f"I found no matching financial activity{f' for {period}' if period else ''}.", "no_activity", ["$.status"])

        period = data.get("period") or data.get("calculation_period")
        if request.tool_name == "get_budget_plan" and data.get("metadata", {}).get("recommendations_available") is False:
            income, expenses, savings = data.get("monthly_income"), data.get("total_expense"), data.get("net_savings")
            if all(isinstance(value, (int, float)) for value in (income, expenses, savings)):
                answer = f"For {period or 'the period checked'}, income was ₹{income:,.2f}, spending was ₹{expenses:,.2f}, and net savings were ₹{savings:,.2f}. I found current budget limits or spending baselines, but need your target monthly savings to suggest new limits. What amount are you aiming to save?"
                return GroundedFallback._answer(answer, "budget_target_required", ["$.monthly_income", "$.total_expense", "$.net_savings", "$.recommended_budgets"])

        if request.tool_name == "get_category_breakdown":
            rows = data.get("categories") or data.get("merchants") or []
            if rows:
                top = rows[:3]
                parts = [f"{row.get('name') or row.get('merchant')}: ₹{row.get('amount', 0):,.2f}" for row in top]
                total = data.get("total_spend")
                summary = f"Your spending breakdown{f' for {period}' if period else ''} is " + ", ".join(parts)
                refs = ["$.categories" if data.get("categories") else "$.merchants"]
                if total is not None:
                    summary += f". Total spending is ₹{total:,.2f}"
                    refs.append("$.total_spend")
                return GroundedFallback._answer(summary + ".", "grounded_fallback", refs)

        if request.tool_name == "compare_periods" and "total_current" in data and "total_previous" in data:
            if data.get("metadata", {}).get("record_count", 0) == 0:
                return GroundedFallback._answer("I couldn't compare those periods because there are no transaction records in either period.", "no_period_data", ["$.metadata.record_count"])
            delta = data.get("variance_amount")
            if delta is not None:
                direction = "increased" if delta > 0 else "decreased" if delta < 0 else "was unchanged"
                answer = f"Spending {direction} by ₹{abs(delta):,.2f} between {data.get('period_previous', 'the earlier period')} and {data.get('period_current', 'the later period')}."
                return GroundedFallback._answer(answer, "grounded_fallback", ["$.variance_amount", "$.period_current", "$.period_previous"])

        if request.tool_name == "find_unusual_transactions":
            anomalies = data.get("anomalies") or []
            if not anomalies:
                return GroundedFallback._answer("I found no transactions flagged for review in the available scan.", "grounded_fallback", ["$.anomalies"])
            count = data.get("anomalies_count", len(anomalies))
            answer = f"I found {count} transaction(s) flagged for review. Would you like details on a specific one?"
            return GroundedFallback._answer(answer, "grounded_fallback", ["$.anomalies_count" if "anomalies_count" in data else "$.anomalies"])

        if request.tool_name == "get_recurring_payments":
            bills = data.get("bills") or []
            if not bills:
                return GroundedFallback._answer("I found no recurring bills in the available records.", "grounded_fallback", ["$.bills"])
            amount = data.get("total_amount_due")
            if isinstance(amount, (int, float)):
                answer = f"I found {len(bills)} recurring bill(s) totaling ₹{amount:,.2f} in the available records."
                return GroundedFallback._answer(answer, "grounded_fallback", ["$.bills", "$.total_amount_due"])

        if request.tool_name == "fetch_portal_receipt_forensics":
            tot = data.get("total_amount")
            portal = data.get("portal", "merchant portal")
            if isinstance(tot, (int, float)):
                return GroundedFallback._answer(f"I retrieved your receipt from {portal} for ₹{tot:,.2f}.", "grounded_fallback", ["$.total_amount"])

        if request.tool_name == "verify_utility_portal_bill":
            bill = data.get("bill_amount")
            due = data.get("due_date", "soon")
            if isinstance(bill, (int, float)):
                return GroundedFallback._answer(f"I verified your utility bill of ₹{bill:,.2f} due on {due}.", "grounded_fallback", ["$.bill_amount", "$.due_date"])

        if request.tool_name == "get_budget_status" and not data.get("budgets"):
            return GroundedFallback._answer("I couldn't find any budget records to compare with spending.", "grounded_fallback", ["$.budgets"])
        if request.tool_name == "get_forecast" and not data.get("points"):
            return GroundedFallback._answer("There isn't enough transaction history to produce a forecast yet.", "insufficient_history", [], "insufficient_history")
        if request.tool_name == "simulate_savings_goal" and data.get("status") == "goal_not_found":
            return GroundedFallback._answer("I couldn't find that savings goal. Which goal would you like to use for the simulation?", "goal_not_found", ["$.status"])
        if request.tool_name == "simulate_savings_goal" and data.get("status") == "goal_selection_required":
            options = data.get("goal_options") or []
            names = ", ".join(str(name) for name in options)
            return GroundedFallback._answer(f"I found more than one savings goal{f': {names}' if names else ''}. Which one should I use?", "goal_selection_required", ["$.goal_options"])
        if request.tool_name == "get_payment_mode_summary":
            amount, count = data.get("total_upi_spend"), data.get("upi_count")
            if isinstance(amount, (int, float)) and isinstance(count, int):
                answer = f"UPI spending is ₹{amount:,.2f} across {count} transaction(s) in the available records."
                return GroundedFallback._answer(answer, "grounded_fallback", ["$.total_upi_spend", "$.upi_count"])

        summary_fields = [
            ("total_expense", "Total spending"), ("total_income", "Income"),
            ("available_balance", "Available balance"), ("total_amount_due", "Bills due"),
            ("total_spend", "Total spending"), ("monthly_savings", "Monthly savings"),
        ]
        for key, label in summary_fields:
            value = data.get(key)
            if isinstance(value, (int, float)):
                answer = f"{label}{f' for {period}' if period else ''}: ₹{value:,.2f}."
                return GroundedFallback._answer(answer, "grounded_fallback", [f"$.{key}"])
        answer = "I retrieved the result, but don't have enough verified detail to summarize it safely. What part would you like me to explain?"
        return GroundedFallback._answer(answer, "no_summarizable_facts")

    @staticmethod
    def _answer(text: str, limitation: str, fact_refs: list[str] | None = None, provider: str = "deterministic") -> GeneratedAnswer:
        return GeneratedAnswer(
            answer=text,
            fact_refs=fact_refs or [],
            prompt_version=PROMPT_VERSION,
            provider=provider,
            used_fallback=True,
            limitation=limitation,
        )


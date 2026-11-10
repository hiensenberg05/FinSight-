"""
FinSight Predictive Advisory Service.
Provides deterministic financial what-if simulations, goal velocity calculations,
and budget-overrun projections with zero LLM math hallucinations.
"""

import calendar
from datetime import date, datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from backend.app.db.models import Transaction, Budget, SavingsGoal


class AdvisoryService:
    """
    Deterministic What-If Simulation Engine.
    Computes exact impact of discretionary expense trims and savings accelerations.
    """

    @staticmethod
    async def _get_anchor_date(db: AsyncSession, user_id: str) -> date:
        stmt = select(func.max(Transaction.transaction_date)).where(Transaction.user_id == user_id)
        max_date = (await db.execute(stmt)).scalar()
        if max_date:
            if isinstance(max_date, str):
                return datetime.strptime(max_date[:10], "%Y-%m-%d").date()
            if isinstance(max_date, datetime):
                return max_date.date()
            if isinstance(max_date, date):
                return max_date
        return date.today()

    @staticmethod
    async def simulate_discretionary_reduction(
        db: AsyncSession,
        user_id: str,
        category: str = "Food & Dining",
        reduction_pct: float = 20.0,
        goal_name: Optional[str] = "Vacation Fund",
    ) -> Dict[str, Any]:
        """
        Calculates monthly savings, annualized savings, and goal completion acceleration
        from a percentage reduction in a target spending category.
        """
        ref_date = await AdvisoryService._get_anchor_date(db, user_id)
        start_date = ref_date.replace(day=1)
        end_date = date(ref_date.year, ref_date.month, calendar.monthrange(ref_date.year, ref_date.month)[1])
        stmt = select(
            func.coalesce(func.sum(func.abs(Transaction.amount_minor)), 0),
            func.count(Transaction.id),
        ).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.category_name.ilike(f"%{category}%"),
                Transaction.transaction_kind == "expense",
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
            )
        )
        spend_row = (await db.execute(stmt)).one()
        cat_minor, category_transaction_count = spend_row[0] or 0, spend_row[1] or 0
        if category_transaction_count == 0:
            return {
                "status": "insufficient_history",
                "category": category,
                "reduction_percentage": max(0.0, min(100.0, float(reduction_pct))),
                "historical_monthly_spend": None,
                "goal_impact": None,
                "baseline_period": today.strftime("%b %Y"),
            }
        current_monthly_spend = cat_minor / 100.0

        # Reduction calculations (deterministic)
        clamped_pct = max(0.0, min(100.0, float(reduction_pct)))
        monthly_savings = round(current_monthly_spend * (clamped_pct / 100.0), 2)
        annualized_savings = round(monthly_savings * 12.0, 2)
        new_monthly_spend = round(current_monthly_spend - monthly_savings, 2)

        # Query savings goal impact
        goal = None
        if goal_name:
            goal_stmt = select(SavingsGoal).where(
                and_(SavingsGoal.user_id == user_id, SavingsGoal.name.ilike(f"%{goal_name}%"))
            )
            goals = (await db.execute(goal_stmt)).scalars().all()
            if len(goals) == 1:
                goal = goals[0]

        goal_data = None
        if goal:
            target = goal.target_amount_minor / 100.0
            current = goal.current_amount_minor / 100.0
            remaining = max(0.0, target - current)
            income_stmt = select(func.coalesce(func.sum(func.abs(Transaction.amount_minor)), 0)).where(
                and_(Transaction.user_id == user_id, Transaction.transaction_kind == "income", Transaction.transaction_date >= start_date, Transaction.transaction_date <= end_date)
            )
            expense_stmt = select(func.coalesce(func.sum(func.abs(Transaction.amount_minor)), 0)).where(
                and_(Transaction.user_id == user_id, Transaction.transaction_kind == "expense", Transaction.transaction_date >= start_date, Transaction.transaction_date <= end_date)
            )
            income_minor = (await db.execute(income_stmt)).scalar() or 0
            expense_minor = (await db.execute(expense_stmt)).scalar() or 0
            base_monthly_contribution = max(0.0, (income_minor - expense_minor) / 100.0) if income_minor else None
            accelerated_monthly = base_monthly_contribution + monthly_savings if base_monthly_contribution is not None else None
            orig_months = round(remaining / base_monthly_contribution, 1) if base_monthly_contribution else None
            accel_months = round(remaining / accelerated_monthly, 1) if accelerated_monthly else None
            months_saved = round(max(0.0, orig_months - accel_months), 1) if orig_months is not None and accel_months is not None else None

            goal_data = {
                "goal_id": goal.id,
                "goal_name": goal.name,
                "target_amount": target,
                "current_amount": current,
                "remaining_amount": remaining,
                "baseline_months_to_complete": orig_months,
                "accelerated_months_to_complete": accel_months,
                "months_saved": months_saved,
                "target_date": goal.target_date_str,
            }

        return {
            "simulation_type": "discretionary_reduction",
            "category": category,
            "reduction_percentage": clamped_pct,
            "historical_monthly_spend": current_monthly_spend,
            "simulated_monthly_spend": new_monthly_spend,
            "monthly_savings": monthly_savings,
            "annualized_savings": annualized_savings,
            "goal_impact": goal_data,
            "slider_bounds": {"min": 0, "max": 50, "step": 5},
            "assumptions": [
                f"Historical baseline spend is based on verified transactions for {category}",
                "Assumes continuous monthly discipline across 12-month projection window",
                "Non-discretionary expenses (rent, utilities) remain constant",
            ],
        }

    @staticmethod
    async def predict_budget_overrun(
        db: AsyncSession,
        user_id: str,
        category: str = "Food & Dining",
    ) -> Dict[str, Any]:
        """
        Projects month-end spending based on current daily run-rate vs category budget limit.
        """
        ref_date = await AdvisoryService._get_anchor_date(db, user_id)
        start_date = ref_date.replace(day=1)
        end_date = date(ref_date.year, ref_date.month, calendar.monthrange(ref_date.year, ref_date.month)[1])
        # Look up budget limit
        b_stmt = select(Budget).where(
            and_(Budget.user_id == user_id, Budget.category_name.ilike(f"%{category}%"))
        )
        budget = (await db.execute(b_stmt)).scalars().first()
        if not budget:
            return {"status": "budget_not_found", "category": category}
        limit = budget.limit_minor / 100.0

        # Query spending so far
        stmt = select(func.coalesce(func.sum(func.abs(Transaction.amount_minor)), 0)).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.category_name.ilike(f"%{category}%"),
                Transaction.transaction_kind == "expense",
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
            )
        )
        spent_minor = (await db.execute(stmt)).scalar() or 0
        current_spent = spent_minor / 100.0
        days_passed = max(1, ref_date.day)
        days_in_month = calendar.monthrange(ref_date.year, ref_date.month)[1]
        daily_pace = current_spent / days_passed
        projected_spend = round(daily_pace * days_in_month, 2)
        overrun = round(max(0.0, projected_spend - limit), 2)
        overrun_pct = round((overrun / limit) * 100, 1) if limit > 0 else 0.0

        return {
            "category": category,
            "budget_limit": limit,
            "current_spent": current_spent,
            "days_elapsed": days_passed,
            "days_in_month": days_in_month,
            "daily_run_rate": round(daily_pace, 2),
            "projected_month_end_spend": projected_spend,
            "is_overrun_projected": projected_spend > limit,
            "overrun_amount": overrun,
            "overrun_percentage": overrun_pct,
            "recommended_daily_cap": round(max(0.0, (limit - current_spent) / max(1, days_in_month - days_passed)), 2),
        }

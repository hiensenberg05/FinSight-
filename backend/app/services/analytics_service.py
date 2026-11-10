import calendar
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from backend.app.db.models import Transaction, BankAccount, RecurringPayment, Budget
from backend.app.schemas.analytics import FinancialHealthMetrics, CategorySpending


CATEGORY_COLORS: Dict[str, str] = {
    "Food & Dining": "#8B5CF6",
    "Bills & Utilities": "#F59E0B",
    "Transportation": "#06B6D4",
    "Entertainment": "#F43F5E",
    "Shopping": "#10B981",
    "Groceries": "#10B981",
    "Subscriptions": "#D946EF",
    "Investment": "#3B82F6",
    "Income": "#10B981",
    "Other": "#64748B",
}


class AnalyticsService:
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
    async def get_health_metrics(db: AsyncSession, user_id: str) -> FinancialHealthMetrics:
        # 1. Total available balance across all accounts
        acc_stmt = select(func.coalesce(func.sum(BankAccount.balance_minor), 0)).where(
            and_(BankAccount.user_id == user_id, BankAccount.is_connected == True)
        )
        total_balance_minor = (await db.execute(acc_stmt)).scalar_one()
        available_balance = total_balance_minor / 100.0

        # Health metrics use the anchor statement month or current calendar month.
        ref_date = await AnalyticsService._get_anchor_date(db, user_id)
        first_of_month = ref_date.replace(day=1)
        end_of_month = date(ref_date.year, ref_date.month, calendar.monthrange(ref_date.year, ref_date.month)[1])

        income_stmt = select(func.coalesce(func.sum(func.abs(Transaction.amount_minor)), 0)).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= first_of_month,
                Transaction.transaction_date <= end_of_month,
                Transaction.transaction_kind == "income",
            )
        )
        monthly_income_minor = (await db.execute(income_stmt)).scalar_one()

        expense_stmt = select(func.coalesce(func.sum(func.abs(Transaction.amount_minor)), 0)).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= first_of_month,
                Transaction.transaction_date <= end_of_month,
                Transaction.transaction_kind == "expense",
            )
        )
        monthly_expense_minor = (await db.execute(expense_stmt)).scalar_one()

        monthly_savings = (monthly_income_minor - monthly_expense_minor) / 100.0

        # 3. Pending bills
        bills_stmt = select(func.coalesce(func.sum(RecurringPayment.amount_minor), 0)).where(
            and_(
                RecurringPayment.user_id == user_id,
                RecurringPayment.status != "paid",
            )
        )
        pending_bills_minor = (await db.execute(bills_stmt)).scalar_one()
        pending_bills = pending_bills_minor / 100.0

        # 4. Deterministic Financial Health Score Calculation (0 - 100)
        # Factor A: Savings rate (ideal is >= 20% of income)
        savings_ratio = (monthly_savings / (monthly_income_minor / 100.0)) if monthly_income_minor > 0 else 0.0
        savings_score = min(100, max(0, int(savings_ratio * 400)))  # 25% savings = 100 pts

        # Factor B: Liquid buffer (months of expenses covered)
        monthly_expense = max(1.0, monthly_expense_minor / 100.0)
        liquidity_months = available_balance / monthly_expense
        liquidity_score = min(100, int((liquidity_months / 3.0) * 100))  # 3 months emergency fund = 100 pts

        # Combined weighted score
        final_score = int(0.45 * savings_score + 0.35 * liquidity_score + 20)
        final_score = min(100, max(20, final_score))

        if monthly_income_minor <= 0:
            final_score = 0
            rating = "Insufficient data"
            summary = "Income records are needed to assess financial health for this period."
        elif final_score >= 75:
            rating = "Excellent"
            summary = "You're spending comfortably within your means! Keep it up or allocate more to your savings goals."
        elif final_score >= 60:
            rating = "Good"
            summary = "Healthy financial footing. Look into trimming recurring subscriptions to accelerate your emergency fund."
        elif final_score >= 45:
            rating = "Fair"
            summary = "Cash reserves are steady, but high discretionary dining expenses are tightening monthly savings."
        else:
            rating = "Poor"
            summary = "Monthly spending is outpacing inflows. Review pending bills and set budget alerts."

        period_str = ref_date.strftime("%b %Y")

        return FinancialHealthMetrics(
            score=final_score,
            rating=rating,
            summary=summary,
            availableBalance=available_balance,
            monthlySavings=monthly_savings,
            pendingBills=pending_bills,
            period=period_str,
        )

    @staticmethod
    async def get_category_spending(
        db: AsyncSession,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[CategorySpending]:
        ref_date = await AnalyticsService._get_anchor_date(db, user_id)
        start_d = start_date or ref_date.replace(day=1)
        end_d = end_date or date(ref_date.year, ref_date.month, calendar.monthrange(ref_date.year, ref_date.month)[1])

        stmt = (
            select(
                Transaction.category_name,
                func.sum(func.abs(Transaction.amount_minor)).label("total_minor"),
            )
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_kind == "expense",
                    Transaction.transaction_date >= start_d,
                    Transaction.transaction_date <= end_d,
                )
            )
            .group_by(Transaction.category_name)
            .order_by(func.sum(func.abs(Transaction.amount_minor)).desc())
        )
        rows = (await db.execute(stmt)).all()

        if not rows:
            return []

        grand_total = sum(r.total_minor for r in rows)
        if grand_total == 0:
            return []

        result = []
        for r in rows:
            amt = round(r.total_minor / 100.0, 2)
            pct = round((r.total_minor / grand_total) * 100)
            color = CATEGORY_COLORS.get(r.category_name, "#8B5CF6")
            result.append(
                CategorySpending(
                    name=r.category_name,
                    amount=amt,
                    currency="₹",
                    percentage=pct,
                    color=color,
                )
            )
        return result

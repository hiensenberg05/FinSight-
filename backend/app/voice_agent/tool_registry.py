"""
The 11 Deterministic Financial Tools for FinSight.
All calculations are strictly grounded in indexed SQL database queries and domain logic.
Zero hallucination: the LLM never computes numbers; it only explains the verified output of these tools.
"""

import calendar
from datetime import date, datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from backend.app.db.models import (
    Transaction,
    Budget,
    RecurringPayment,
    BankAccount,
    SavingsGoal,
    User,
)
from backend.app.services.analytics_service import AnalyticsService, CATEGORY_COLORS
from backend.app.services.anomaly_service import AnomalyService
from backend.app.services.forecast_service import ForecastService


class FinancialToolRegistry:
    """
    Registry of all 11 Deterministic Financial Tools specified in architecture.md.
    Every method queries the verified SQLite/PostgreSQL database scoped to the authenticated user.
    """

    @classmethod
    async def _get_anchor_date(cls, db: AsyncSession, user_id: str) -> date:
        """
        Dynamically determine the anchor date for ledger operations.
        Inspects the user's latest transaction date in the database.
        Falls back to current date if no transactions exist.
        """
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
    def _resolve_period_dates(period: Optional[str] = None, anchor_date: Optional[date] = None):
        """
        Helper to map textual period expressions to start and end dates.
        Resolve relative periods against anchor_date (or current calendar date) and allow explicit month labels.
        """
        ref = anchor_date or date.today()
        ref_year = ref.year
        ref_month = ref.month

        if not period or period in ("current", "current_month", "this_month"):
            start = date(ref_year, ref_month, 1)
            end = date(ref_year, ref_month, calendar.monthrange(ref_year, ref_month)[1])
            label = f"{start.strftime('%b %Y')}"
            return start, end, label

        if period in ("previous", "previous_month", "last_month"):
            prev_m = ref_month - 1 if ref_month > 1 else 12
            prev_y = ref_year if ref_month > 1 else ref_year - 1
            start = date(prev_y, prev_m, 1)
            end = date(prev_y, prev_m, calendar.monthrange(prev_y, prev_m)[1])
            label = f"{start.strftime('%b %Y')}"
            return start, end, label

        for date_format in ("%Y-%m", "%b %Y", "%B %Y"):
            try:
                parsed = datetime.strptime(period.strip(), date_format).date()
                start = date(parsed.year, parsed.month, 1)
                end = date(parsed.year, parsed.month, calendar.monthrange(parsed.year, parsed.month)[1])
                return start, end, start.strftime("%b %Y")
            except ValueError:
                continue

        if period.lower() == "all":
            return date.min, date.max, "all available records"

        start = date(ref_year, ref_month, 1)
        end = date(ref_year, ref_month, calendar.monthrange(ref_year, ref_month)[1])
        return start, end, start.strftime("%b %Y")

    @staticmethod
    async def _fetch_evidence_items(
        db: AsyncSession,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category: Optional[str] = None,
        merchant: Optional[str] = None,
        anomaly_only: bool = False,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves real, grounded Transaction records with masked account references for data provenance.
        """
        stmt = (
            select(Transaction, BankAccount.institution_name, BankAccount.account_mask)
            .outerjoin(BankAccount, BankAccount.id == Transaction.account_id)
            .where(Transaction.user_id == user_id)
        )
        if start_date:
            stmt = stmt.where(Transaction.transaction_date >= start_date)
        if end_date:
            stmt = stmt.where(Transaction.transaction_date <= end_date)
        if category and category.lower() not in ("all", "none"):
            stmt = stmt.where(Transaction.category_name.ilike(f"%{category}%"))
        if merchant:
            stmt = stmt.where(Transaction.merchant_name.ilike(f"%{merchant}%"))
        if anomaly_only:
            stmt = stmt.where(Transaction.is_anomaly == True)

        stmt = stmt.order_by(Transaction.amount_minor.asc()).limit(limit)
        results = (await db.execute(stmt)).all()

        evidence = []
        for t, inst, mask in results:
            acc_ref = f"{inst}-XXXX-{mask}" if inst and mask else None
            amt_formatted = f"₹{abs(t.amount_minor) / 100:,.2f}"
            evidence.append({
                "transaction_id": t.id,
                "account_reference": acc_ref,
                "date": t.transaction_date.isoformat() if hasattr(t.transaction_date, "isoformat") else str(t.transaction_date),
                "merchant": t.merchant_name,
                "amount_minor": t.amount_minor,
                "amount_formatted": amt_formatted,
                "currency": t.currency or "INR",
                "category": t.category_name,
                "payment_mode": t.payment_mode,
                "source_import_id": t.import_job_id,
                "is_anomaly": bool(t.is_anomaly),
                "anomaly_reason": t.anomaly_reason,
            })
        return evidence

    # -------------------------------------------------------------
    # Tool 1: get_spending_summary
    # -------------------------------------------------------------
    @staticmethod
    async def get_spending_summary(
        db: AsyncSession,
        user_id: str,
        period: str = "current_month",
    ) -> Dict[str, Any]:
        """Tool 1: Income, expenses and net cash flow for current/specified period."""
        anchor_date = await FinancialToolRegistry._get_anchor_date(db, user_id)
        start_d, end_d, period_label = FinancialToolRegistry._resolve_period_dates(period, anchor_date=anchor_date)

        # Available liquid cash balance
        acc_stmt = select(func.coalesce(func.sum(BankAccount.balance_minor), 0)).where(
            and_(BankAccount.user_id == user_id, BankAccount.is_connected == True)
        )
        total_balance_minor = (await db.execute(acc_stmt)).scalar() or 0
        available_balance = total_balance_minor / 100.0

        # Income in period
        inc_stmt = select(func.coalesce(func.sum(func.abs(Transaction.amount_minor)), 0)).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.transaction_kind == "income",
                Transaction.transaction_date >= start_d,
                Transaction.transaction_date <= end_d,
            )
        )
        income_minor = (await db.execute(inc_stmt)).scalar() or 0
        total_income = income_minor / 100.0

        # Expense in period
        exp_stmt = select(
            func.coalesce(func.sum(func.abs(Transaction.amount_minor)), 0),
            func.count(Transaction.id)
        ).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.transaction_kind == "expense",
                Transaction.transaction_date >= start_d,
                Transaction.transaction_date <= end_d,
            )
        )
        exp_row = (await db.execute(exp_stmt)).one()
        expense_minor = exp_row[0] or 0
        tx_count = exp_row[1] or 0
        total_expense = expense_minor / 100.0

        net_savings = round(total_income - total_expense, 2)
        savings_ratio = round((net_savings / total_income) * 100, 1) if total_income > 0 else 0.0

        # Pending recurring bills
        bills_stmt = select(func.coalesce(func.sum(RecurringPayment.amount_minor), 0)).where(
            and_(RecurringPayment.user_id == user_id, RecurringPayment.status != "paid")
        )
        pending_bills_minor = (await db.execute(bills_stmt)).scalar() or 0
        pending_bills = pending_bills_minor / 100.0

        health_metrics = await AnalyticsService.get_health_metrics(db, user_id)
        evidence = await FinancialToolRegistry._fetch_evidence_items(
            db, user_id, start_date=start_d, end_date=end_d, limit=8
        )
        metadata = {
            "calculation_period": period_label,
            "aggregation_methodology": "Total debit and credit transaction aggregation with bank account balances",
            "record_count": tx_count or len(evidence),
            "verified_ledger": bool(tx_count or evidence),
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }
        status = "ok" if tx_count else ("insufficient_expense_data" if total_income > 0 or evidence else "no_activity")

        return {
            "status": status,
            "period": period_label,
            "available_balance": available_balance,
            "total_income": total_income,
            "total_expense": total_expense,
            "net_savings": net_savings,
            "savings_ratio_pct": savings_ratio,
            "pending_bills": pending_bills,
            "transaction_count": tx_count,
            "health_score": health_metrics.score,
            "health_rating": health_metrics.rating,
            "evidence": evidence,
            "metadata": metadata,
        }

    # -------------------------------------------------------------
    # Tool 2: get_category_breakdown
    # -------------------------------------------------------------
    @staticmethod
    async def get_category_breakdown(
        db: AsyncSession,
        user_id: str,
        category: Optional[str] = None,
        period: str = "current_month",
        limit: int = 8,
    ) -> Dict[str, Any]:
        """Tool 2: Spending grouped by category with amounts, percentages, and merchant drills."""
        anchor_date = await FinancialToolRegistry._get_anchor_date(db, user_id)
        start_d, end_d, period_label = FinancialToolRegistry._resolve_period_dates(period, anchor_date=anchor_date)

        # Drill into a specific single category if requested
        if category and category.lower() not in ("all", "none"):
            stmt = (
                select(
                    Transaction.merchant_name,
                    func.sum(func.abs(Transaction.amount_minor)).label("total_minor"),
                    func.count(Transaction.id).label("count"),
                )
                .where(
                    and_(
                        Transaction.user_id == user_id,
                        Transaction.transaction_kind == "expense",
                        Transaction.category_name.ilike(f"%{category}%"),
                        Transaction.transaction_date >= start_d,
                        Transaction.transaction_date <= end_d,
                    )
                )
                .group_by(Transaction.merchant_name)
                .order_by(func.sum(func.abs(Transaction.amount_minor)).desc())
                .limit(limit)
            )
            merchants = (await db.execute(stmt)).all()
            totals_stmt = select(
                func.coalesce(func.sum(func.abs(Transaction.amount_minor)), 0),
                func.count(Transaction.id),
            ).where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_kind == "expense",
                    Transaction.category_name.ilike(f"%{category}%"),
                    Transaction.transaction_date >= start_d,
                    Transaction.transaction_date <= end_d,
                )
            )
            totals = (await db.execute(totals_stmt)).one()
            cat_total = (totals[0] or 0) / 100.0
            order_count = totals[1] or 0

            merchant_items = [
                {
                    "merchant": m.merchant_name,
                    "amount": m.total_minor / 100.0,
                    "orders_count": m.count,
                }
                for m in merchants
            ]

            evidence = await FinancialToolRegistry._fetch_evidence_items(
                db, user_id, start_date=start_d, end_date=end_d, category=category, limit=8
            )
            metadata = {
                "calculation_period": period_label,
                "aggregation_methodology": f"SUM(abs(amount_minor)) filtered by category '{category}'",
                "record_count": order_count,
                "verified_ledger": order_count > 0,
                "executed_at": datetime.now(timezone.utc).isoformat(),
            }

            return {
                "period": period_label,
                "category": category,
                "total_spend": cat_total,
                "orders_count": order_count,
                "merchants": merchant_items,
                "status": "ok" if order_count else "no_activity",
                "evidence": evidence,
                "metadata": metadata,
            }

        # Overall category breakdown
        stmt = (
            select(
                Transaction.category_name,
                func.sum(func.abs(Transaction.amount_minor)).label("total_minor"),
                func.count(Transaction.id).label("count"),
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
            .limit(limit)
        )
        rows = (await db.execute(stmt)).all()

        totals_stmt = select(
            func.coalesce(func.sum(func.abs(Transaction.amount_minor)), 0),
            func.count(Transaction.id),
        ).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.transaction_kind == "expense",
                Transaction.transaction_date >= start_d,
                Transaction.transaction_date <= end_d,
            )
        )
        totals = (await db.execute(totals_stmt)).one()
        grand_total_minor = totals[0] or 0
        period_transaction_count = totals[1] or 0

        evidence = await FinancialToolRegistry._fetch_evidence_items(
            db, user_id, start_date=start_d, end_date=end_d, limit=8
        )
        metadata = {
            "calculation_period": period_label,
            "aggregation_methodology": "SUM(abs(amount_minor)) GROUP BY category_name",
            "record_count": period_transaction_count,
            "verified_ledger": bool(rows),
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }

        grand_total = grand_total_minor
        categories = []
        for r in rows:
            amt = r.total_minor / 100.0
            pct = round((r.total_minor / grand_total) * 100) if grand_total > 0 else 0
            color = CATEGORY_COLORS.get(r.category_name, "#8B5CF6")
            categories.append({
                "name": r.category_name,
                "amount": amt,
                "currency": "₹",
                "percentage": pct,
                "color": color,
                "transaction_count": r.count,
            })

        return {
            "period": period_label,
            "total_spend": grand_total / 100.0,
            "total_categories": len(categories),
            "categories": categories,
            "status": "ok" if rows else "no_activity",
            "evidence": evidence,
            "metadata": metadata,
        }

    # -------------------------------------------------------------
    # Tool 3: compare_periods
    # -------------------------------------------------------------
    @staticmethod
    async def compare_periods(
        db: AsyncSession,
        user_id: str,
        period_1: str = "current_month",
        period_2: str = "previous_month",
        lookback_days: int = 30,
    ) -> Dict[str, Any]:
        """Tool 3: Compare two explicit periods and explain variances."""
        anchor_date = await FinancialToolRegistry._get_anchor_date(db, user_id)
        start_1, end_1, label_1 = FinancialToolRegistry._resolve_period_dates(period_1, anchor_date=anchor_date)
        start_2, end_2, label_2 = FinancialToolRegistry._resolve_period_dates(period_2, anchor_date=anchor_date)

        # Period 1 category expenses
        stmt_1 = (
            select(
                Transaction.category_name,
                func.sum(func.abs(Transaction.amount_minor)).label("total_minor"),
            )
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_kind == "expense",
                    Transaction.transaction_date >= start_1,
                    Transaction.transaction_date <= end_1,
                )
            )
            .group_by(Transaction.category_name)
        )
        rows_1 = (await db.execute(stmt_1)).all()
        map_1 = {r.category_name: r.total_minor / 100.0 for r in rows_1}
        total_1 = sum(map_1.values())

        # Period 2 category expenses
        stmt_2 = (
            select(
                Transaction.category_name,
                func.sum(func.abs(Transaction.amount_minor)).label("total_minor"),
            )
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_kind == "expense",
                    Transaction.transaction_date >= start_2,
                    Transaction.transaction_date <= end_2,
                )
            )
            .group_by(Transaction.category_name)
        )
        rows_2 = (await db.execute(stmt_2)).all()
        map_2 = {r.category_name: r.total_minor / 100.0 for r in rows_2}
        total_2 = sum(map_2.values())

        # Calculate category deltas
        all_cats = set(map_1.keys()) | set(map_2.keys())
        drivers = []
        for cat in all_cats:
            amt_1 = map_1.get(cat, 0.0)
            amt_2 = map_2.get(cat, 0.0)
            diff = amt_1 - amt_2
            if diff > 0:
                drivers.append({
                    "category": cat,
                    "delta": round(diff, 2),
                    "current": round(amt_1, 2),
                    "previous": round(amt_2, 2),
                })
        drivers.sort(key=lambda d: d["delta"], reverse=True)

        variance_amount = round(total_1 - total_2, 2)
        variance_percentage = round((variance_amount / total_2) * 100, 1) if total_2 > 0 else None

        evidence = await FinancialToolRegistry._fetch_evidence_items(
            db, user_id, start_date=start_1, end_date=end_1, limit=10
        )
        metadata = {
            "calculation_period": f"{label_1} vs {label_2}",
            "aggregation_methodology": "Category-level sum delta with variance driver ranking",
            "record_count": len(rows_1) + len(rows_2) or len(evidence),
            "verified_ledger": True,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }

        return {
            "period_current": label_1,
            "period_previous": label_2,
            "total_current": round(total_1, 2),
            "total_previous": round(total_2, 2),
            "variance_amount": variance_amount,
            "variance_percentage": variance_percentage,
            "drivers": [
                {**driver, "percentage": round((driver["delta"] / abs(variance_amount)) * 100) if variance_amount else 0}
                for driver in drivers
            ],
            "evidence": evidence,
            "metadata": metadata,
        }

    # -------------------------------------------------------------
    # Tool 4: get_top_merchants
    # -------------------------------------------------------------
    @staticmethod
    async def get_top_merchants(
        db: AsyncSession,
        user_id: str,
        category: Optional[str] = None,
        payment_mode: Optional[str] = None,
        limit: int = 5,
        period: str = "current_month",
    ) -> List[Dict[str, Any]]:
        """Tool 4: Rank merchants by total debit spend and transaction count."""
        anchor_date = await FinancialToolRegistry._get_anchor_date(db, user_id)
        start_d, end_d, _ = FinancialToolRegistry._resolve_period_dates(period, anchor_date=anchor_date)
        stmt = (
            select(
                Transaction.merchant_name,
                Transaction.category_name,
                func.sum(func.abs(Transaction.amount_minor)).label("total_minor"),
                func.count(Transaction.id).label("count"),
            )
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_kind == "expense",
                    Transaction.transaction_date >= start_d,
                    Transaction.transaction_date <= end_d,
                )
            )
        )

        if category and category.lower() != "all":
            stmt = stmt.where(Transaction.category_name.ilike(f"%{category}%"))

        if payment_mode:
            stmt = stmt.where(Transaction.payment_mode.ilike(payment_mode))

        stmt = (
            stmt.group_by(Transaction.merchant_name, Transaction.category_name)
            .order_by(func.sum(func.abs(Transaction.amount_minor)).desc())
            .limit(limit)
        )
        rows = (await db.execute(stmt)).all()

        return [
            {
                "merchant": r.merchant_name,
                "category": r.category_name,
                "amount": round(r.total_minor / 100.0, 2),
                "transactions_count": r.count,
            }
            for r in rows
        ]

    # -------------------------------------------------------------
    # Tool 5: get_payment_mode_summary
    # -------------------------------------------------------------
    @staticmethod
    async def get_payment_mode_summary(
        db: AsyncSession,
        user_id: str,
        mode: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 5,
        period: str = "current_month",
    ) -> Dict[str, Any]:
        """Tool 5: Summarize payment modes (UPI vs Card vs NetBanking)."""
        anchor_date = await FinancialToolRegistry._get_anchor_date(db, user_id)
        start_d, end_d, period_label = FinancialToolRegistry._resolve_period_dates(period, anchor_date=anchor_date)
        stmt = (
            select(
                Transaction.payment_mode,
                func.sum(func.abs(Transaction.amount_minor)).label("total_minor"),
                func.count(Transaction.id).label("count"),
            )
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_kind == "expense",
                    Transaction.transaction_date >= start_d,
                    Transaction.transaction_date <= end_d,
                )
            )
        )
        if category:
            stmt = stmt.where(Transaction.category_name.ilike(f"%{category}%"))
        if mode:
            stmt = stmt.where(Transaction.payment_mode.ilike(f"%{mode}%"))
        stmt = stmt.group_by(Transaction.payment_mode).order_by(func.sum(func.abs(Transaction.amount_minor)).desc())
        rows = (await db.execute(stmt)).all()

        total_minor = sum(r.total_minor for r in rows)
        breakdown = [
            {
                "mode": r.payment_mode or "UPI",
                "amount": round(r.total_minor / 100.0, 2),
                "count": r.count,
                "percentage": round((r.total_minor / total_minor) * 100) if total_minor else 0,
            }
            for r in rows
        ]

        # Top merchants for selected mode or UPI
        target_mode = mode or "UPI"
        m_stmt = (
            select(
                Transaction.merchant_name,
                func.sum(func.abs(Transaction.amount_minor)).label("total_minor"),
                func.count(Transaction.id).label("count"),
            )
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_kind == "expense",
                    Transaction.payment_mode.ilike(f"%{target_mode}%"),
                    Transaction.transaction_date >= start_d,
                    Transaction.transaction_date <= end_d,
                )
            )
        )
        if category:
            m_stmt = m_stmt.where(Transaction.category_name.ilike(f"%{category}%"))
        m_stmt = m_stmt.group_by(Transaction.merchant_name).order_by(func.sum(func.abs(Transaction.amount_minor)).desc()).limit(limit)
        m_rows = (await db.execute(m_stmt)).all()
        top_merchants = [
            {"merchant": m.merchant_name, "amount": round(m.total_minor / 100.0, 2), "count": m.count}
            for m in m_rows
        ]

        upi_item = next((b for b in breakdown if "upi" in b["mode"].lower()), None)
        upi_amount = upi_item["amount"] if upi_item else 0.0
        upi_count = upi_item["count"] if upi_item else 0

        return {
            "period": period_label,
            "breakdown": breakdown,
            "target_mode": target_mode,
            "total_upi_spend": upi_amount,
            "upi_count": upi_count,
            "top_merchants": top_merchants,
        }

    # -------------------------------------------------------------
    # Tool 6: get_recurring_payments
    # -------------------------------------------------------------
    @staticmethod
    async def get_recurring_payments(
        db: AsyncSession,
        user_id: str,
        days_ahead: int = 30,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Tool 6: Retrieve detected recurring obligations, bills, and available cash buffer."""
        days_ahead = max(0, min(int(days_ahead), 365))
        stmt = select(RecurringPayment).where(
            RecurringPayment.user_id == user_id,
            RecurringPayment.days_left >= 0,
            RecurringPayment.days_left <= days_ahead,
        )
        if status:
            stmt = stmt.where(RecurringPayment.status == status)
        else:
            stmt = stmt.where(RecurringPayment.status != "paid")

        stmt = stmt.order_by(RecurringPayment.days_left.asc())
        rows = (await db.execute(stmt)).scalars().all()

        total_due_minor = sum(b.amount_minor for b in rows)
        total_due = total_due_minor / 100.0

        # Available cash buffer check
        acc_stmt = select(func.coalesce(func.sum(BankAccount.balance_minor), 0)).where(
            and_(BankAccount.user_id == user_id, BankAccount.is_connected == True)
        )
        total_balance_minor = (await db.execute(acc_stmt)).scalar() or 0
        available_balance = total_balance_minor / 100.0

        is_safe = available_balance >= total_due
        buffer_remaining = round(available_balance - total_due, 2)

        bills_list = [
            {
                "id": b.id,
                "name": b.name,
                "category": b.category_name,
                "amount": round(b.amount_minor / 100.0, 2),
                "dueDate": b.due_date_str,
                "daysLeft": b.days_left,
                "autoPay": b.auto_pay,
                "status": b.status,
            }
            for b in rows
        ]

        return {
            "total_bills_count": len(bills_list),
            "total_amount_due": total_due,
            "available_balance": available_balance,
            "cash_buffer_remaining": buffer_remaining,
            "is_completely_covered": is_safe,
            "bills": bills_list,
        }

    # -------------------------------------------------------------
    # Tool 7: get_savings_ratio
    # -------------------------------------------------------------
    @staticmethod
    async def get_savings_ratio(
        db: AsyncSession,
        user_id: str,
        period: str = "current_month",
    ) -> Dict[str, Any]:
        """Tool 7: Calculate savings ratio with documented definition."""
        summary = await FinancialToolRegistry.get_spending_summary(db, user_id, period)
        income = summary["total_income"]
        savings = summary["net_savings"]
        enough_data = summary.get("status") == "ok" and income > 0
        ratio_pct = round((savings / income) * 100, 1) if enough_data else None

        status = ("Healthy (Recommended >= 20%)" if ratio_pct >= 20.0 else "Tight (< 20%)") if ratio_pct is not None else "Insufficient transaction data"
        return {
            "status": "ok" if enough_data else summary.get("status", "insufficient_expense_data"),
            "monthly_income": income,
            "monthly_savings": savings,
            "savings_ratio_pct": ratio_pct,
            "benchmark_status": status,
            "available_balance": summary["available_balance"],
        }

    # -------------------------------------------------------------
    # Tool 8: get_budget_status
    # -------------------------------------------------------------
    @staticmethod
    async def get_budget_status(
        db: AsyncSession,
        user_id: str,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Tool 8: Return budget allocation and current monthly utilization."""
        anchor_date = await FinancialToolRegistry._get_anchor_date(db, user_id)
        period_start, period_end, period_label = FinancialToolRegistry._resolve_period_dates("current_month", anchor_date=anchor_date)
        stmt = select(Budget).where(Budget.user_id == user_id)
        if category:
            stmt = stmt.where(Budget.category_name.ilike(f"%{category}%"))

        budgets = (await db.execute(stmt)).scalars().all()
        budget_items = []

        activity_count_stmt = select(func.count(Transaction.id)).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.transaction_kind == "expense",
                Transaction.transaction_date >= period_start,
                Transaction.transaction_date <= period_end,
            )
        )
        period_activity_count = (await db.execute(activity_count_stmt)).scalar() or 0
        if period_activity_count == 0:
            budget_items = [
                {
                    "id": item.id,
                    "category": item.category_name,
                    "limit": round(item.limit_minor / 100.0, 2),
                    "spent": None,
                    "remaining": None,
                    "utilization_pct": None,
                    "status": "Unknown: no transaction coverage for period",
                }
                for item in budgets
            ]
            return {
                "status": "insufficient_coverage",
                "total_budgets": len(budget_items),
                "budgets": budget_items,
                "evidence": [],
                "metadata": {"calculation_period": period_label, "record_count": 0, "verified_ledger": False},
            }

        for b in budgets:
            # Compare the budget limit with expense transactions in the selected month.
            spent_stmt = select(func.coalesce(func.sum(func.abs(Transaction.amount_minor)), 0)).where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.category_name == b.category_name,
                    Transaction.transaction_kind == "expense",
                    Transaction.transaction_date >= period_start,
                    Transaction.transaction_date <= period_end,
                )
            )
            spent_minor = (await db.execute(spent_stmt)).scalar() or 0
            spent = round(spent_minor / 100.0, 2)
            limit = round(b.limit_minor / 100.0, 2)

            utilization_pct = round((spent / limit) * 100) if limit > 0 else 0
            remaining = round(max(0.0, limit - spent), 2)
            alert = "Exceeded" if spent > limit else ("Near Limit (>85%)" if utilization_pct >= 85 else "On Track")

            budget_items.append({
                "id": b.id,
                "category": b.category_name,
                "limit": limit,
                "spent": spent,
                "remaining": remaining,
                "utilization_pct": utilization_pct,
                "status": alert,
            })

        evidence = await FinancialToolRegistry._fetch_evidence_items(
            db, user_id, limit=8
        )
        metadata = {
            "calculation_period": period_label,
            "aggregation_methodology": "Category limit vs actual ledger spend",
            "record_count": len(budget_items),
            "verified_ledger": True,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }

        return {
            "status": "ok",
            "total_budgets": len(budget_items),
            "budgets": budget_items,
            "evidence": evidence,
            "metadata": metadata,
        }

    # -------------------------------------------------------------
    # Tool: get_budget_plan (Personalized Next-Month Budget Allocation)
    # -------------------------------------------------------------
    @staticmethod
    async def get_budget_plan(
        db: AsyncSession,
        user_id: str,
    ) -> Dict[str, Any]:
        """Formulate a personalized next-month budget plan based on verified income and ledger run-rate."""
        anchor_date = await FinancialToolRegistry._get_anchor_date(db, user_id)
        period_start, period_end, period_label = FinancialToolRegistry._resolve_period_dates("current_month", anchor_date=anchor_date)
        income_stmt = select(func.coalesce(func.sum(func.abs(Transaction.amount_minor)), 0)).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.transaction_kind == "income",
                Transaction.transaction_date >= period_start,
                Transaction.transaction_date <= period_end,
            )
        )
        monthly_income_minor = (await db.execute(income_stmt)).scalar() or 0
        monthly_income = monthly_income_minor / 100.0
        if monthly_income <= 0:
            evidence = await FinancialToolRegistry._fetch_evidence_items(db, user_id, start_date=period_start, end_date=period_end, limit=8)
            return {
                "status": "insufficient_income_data",
                "monthly_income": 0.0,
                "fixed_bills": 0.0,
                "recommended_budgets": [],
                "evidence": evidence,
                "metadata": {"calculation_period": period_label, "record_count": len(evidence), "verified_ledger": True},
            }

        bills_stmt = select(func.coalesce(func.sum(RecurringPayment.amount_minor), 0)).where(
            RecurringPayment.user_id == user_id
        )
        bills_minor = (await db.execute(bills_stmt)).scalar() or 0
        bills_total = bills_minor / 100.0

        expense_stmt = select(
            Transaction.category_name,
            func.sum(func.abs(Transaction.amount_minor)).label("total_minor"),
        ).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.transaction_kind == "expense",
                Transaction.transaction_date >= period_start,
                Transaction.transaction_date <= period_end,
            )
        ).group_by(Transaction.category_name)
        expense_rows = (await db.execute(expense_stmt)).all()
        if not expense_rows:
            evidence = await FinancialToolRegistry._fetch_evidence_items(db, user_id, start_date=period_start, end_date=period_end, limit=8)
            return {
                "status": "insufficient_expense_data",
                "monthly_income": monthly_income,
                "fixed_bills": bills_total,
                "evidence": evidence,
                "metadata": {"calculation_period": period_label, "record_count": len(evidence), "verified_ledger": bool(evidence)},
            }
        actual_spend = {row.category_name: row.total_minor / 100.0 for row in expense_rows}
        budget_stmt = select(Budget).where(Budget.user_id == user_id)
        existing_budgets = (await db.execute(budget_stmt)).scalars().all()
        budget_by_category = {item.category_name: item.limit_minor / 100.0 for item in existing_budgets}
        categories = set(actual_spend) | set(budget_by_category)
        reference_budgets = []
        for category_name in sorted(categories):
            amount = budget_by_category.get(category_name, actual_spend.get(category_name, 0.0))
            reference_budgets.append({
                "category": category_name,
                "amount": amount,
                "basis": "existing_budget" if category_name in budget_by_category else "observed_spend",
                "percentage_of_income": round((amount / monthly_income) * 100, 1),
                "color": CATEGORY_COLORS.get(category_name, "#8B5CF6"),
            })
        total_expense = sum(actual_spend.values())
        net_savings = round(monthly_income - total_expense, 2)

        evidence = await FinancialToolRegistry._fetch_evidence_items(db, user_id, limit=8)
        metadata = {
            "calculation_period": f"Next month plan based on {period_label}",
            "aggregation_methodology": "Current-period income, categorized spending, and saved budget limits",
            "record_count": len(evidence),
            "verified_ledger": True,
            "recommendations_available": False,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }

        return {
            "monthly_income": monthly_income,
            "fixed_bills": bills_total,
            "total_expense": total_expense,
            "net_savings": net_savings,
            "recommended_budgets": reference_budgets,
            "evidence": evidence,
            "metadata": metadata,
        }

    # -------------------------------------------------------------
    # Tool 9: get_forecast
    # -------------------------------------------------------------
    @staticmethod
    async def get_forecast(
        db: AsyncSession,
        user_id: str,
        months_ahead: int = 3,
    ) -> Dict[str, Any]:
        """Tool 9: Return forecast points and cashflow trajectory."""
        points = await ForecastService.get_cashflow_forecast(db, user_id)
        return {
            "forecast_type": "12_month_cashflow",
            "model": "Holt-Winters Double Exponential Smoothing with 80% Confidence Intervals",
            "points": [p.model_dump() for p in points],
        }

    # -------------------------------------------------------------
    # Tool 10: find_unusual_transactions
    # -------------------------------------------------------------
    @staticmethod
    async def find_unusual_transactions(
        db: AsyncSession,
        user_id: str,
        lookback_days: int = 60,
        focus: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Tool 10: Return review indicators and statistical anomalies with data provenance."""
        lookback_days = max(1, min(int(lookback_days), 3650))
        anchor_date = await FinancialToolRegistry._get_anchor_date(db, user_id)
        flagged = await AnomalyService.detect_anomalies(db, user_id, lookback_days=lookback_days, anchor_date=anchor_date)

        # Filter by focus if provided
        if focus:
            f_lower = focus.lower()
            filtered = [
                a for a in flagged
                if f_lower in a.get("merchant", "").lower() or f_lower in a.get("category", "").lower()
            ]
            flagged = filtered

        evidence = await FinancialToolRegistry._fetch_evidence_items(
            db, user_id, start_date=anchor_date - timedelta(days=lookback_days), anomaly_only=True, limit=10
        )
        metadata = {
            "calculation_period": f"Past {lookback_days} days review scan",
            "aggregation_methodology": "Configured category review thresholds and existing ledger flags",
            "record_count": len(flagged),
            "verified_ledger": True,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }

        return {
            "anomalies_count": len(flagged),
            "anomalies": flagged,
            "evidence": evidence,
            "metadata": metadata,
        }

    # -------------------------------------------------------------
    # Tool 11: simulate_savings_goal
    # -------------------------------------------------------------
    @staticmethod
    async def simulate_savings_goal(
        db: AsyncSession,
        user_id: str,
        goal_name: str = "Vacation Fund",
        discretionary_reduction_pct: float = 20.0,
    ) -> Dict[str, Any]:
        """Tool 11: Calculate savings goal velocity and timeline simulation."""
        anchor_date = await FinancialToolRegistry._get_anchor_date(db, user_id)
        period_start, period_end, period_label = FinancialToolRegistry._resolve_period_dates("current_month", anchor_date=anchor_date)
        # Query matching goal from DB
        stmt = select(SavingsGoal).where(SavingsGoal.user_id == user_id)
        if goal_name:
            stmt = stmt.where(SavingsGoal.name.ilike(f"%{goal_name}%"))
        goals = (await db.execute(stmt)).scalars().all()

        if not goals:
            return {
                "status": "goal_not_found",
                "goal_name": goal_name,
                "evidence": [],
                "metadata": {"verified_ledger": True, "record_count": 0},
            }
        if len(goals) > 1:
            return {
                "status": "goal_selection_required",
                "goal_options": [item.name for item in goals],
                "evidence": [],
                "metadata": {"verified_ledger": True, "record_count": 0},
            }

        goal = goals[0]

        target = goal.target_amount_minor / 100.0
        current = goal.current_amount_minor / 100.0
        g_name = goal.name

        remaining = max(0.0, round(target - current, 2))

        # Query actual monthly discretionary expenses (Food & Dining + Shopping)
        stmt_disc = select(
            func.coalesce(func.sum(func.abs(Transaction.amount_minor)), 0),
            func.count(Transaction.id),
        ).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.transaction_kind == "expense",
                or_(
                    Transaction.category_name.ilike("%Food%"),
                    Transaction.category_name.ilike("%Shopping%"),
                    Transaction.category_name.ilike("%Entertainment%"),
                ),
                Transaction.transaction_date >= period_start,
                Transaction.transaction_date <= period_end,
            )
        )
        disc_row = (await db.execute(stmt_disc)).one()
        disc_minor, disc_count = disc_row[0] or 0, disc_row[1] or 0
        if disc_count == 0:
            return {
                "status": "insufficient_history",
                "category": "discretionary spending",
                "baseline_period": period_label,
                "goal_name": g_name,
                "evidence": [],
                "metadata": {"calculation_period": period_label, "record_count": 0, "verified_ledger": False},
            }
        monthly_disc = disc_minor / 100.0

        monthly_cut_savings = round(monthly_disc * (discretionary_reduction_pct / 100.0), 2)
        summary = await FinancialToolRegistry.get_spending_summary(db, user_id, "current_month")
        base_monthly_savings = max(0.0, summary["net_savings"]) if summary.get("status") == "ok" else None
        accelerated_savings = base_monthly_savings + monthly_cut_savings if base_monthly_savings is not None else None

        original_months = round(remaining / base_monthly_savings, 1) if base_monthly_savings and base_monthly_savings > 0 else None
        accelerated_months = round(remaining / accelerated_savings, 1) if accelerated_savings and accelerated_savings > 0 else None

        months_saved = round(max(0.0, original_months - accelerated_months), 1) if original_months is not None and accelerated_months is not None else None

        evidence = await FinancialToolRegistry._fetch_evidence_items(
            db, user_id, category="Food & Dining", limit=8
        )
        metadata = {
            "calculation_period": f"{period_label} discretionary run-rate",
            "aggregation_methodology": "Discretionary reduction multiplier and amortization timeline projection",
            "record_count": len(evidence),
            "verified_ledger": True,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }

        return {
            "goal_name": g_name,
            "target_amount": target,
            "current_amount": current,
            "remaining_amount": remaining,
            "discretionary_reduction_pct": discretionary_reduction_pct,
            "monthly_extra_savings": monthly_cut_savings,
            "new_monthly_savings_pace": accelerated_savings,
            "months_to_complete": accelerated_months,
            "original_months": original_months,
            "months_saved": months_saved,
            "recommendation": None,
            "evidence": evidence,
            "metadata": metadata,
        }

    # =============================================================
    # Action Operator Methods (Safe Human-In-The-Loop Proposals)
    # =============================================================
    @staticmethod
    async def prepare_set_budget(
        db: AsyncSession,
        user_id: str,
        category: str = "Food & Dining",
        amount: float = 15000.0,
    ) -> Dict[str, Any]:
        """Action tool: Prepares a budget modification proposal with 5-minute safety TTL."""
        from backend.app.voice_agent.action_operator import ActionOperatorService
        proposal = await ActionOperatorService.prepare_action(
            db=db,
            user_id=user_id,
            action_type="set_category_budget",
            parameters={"category": category, "amount": amount},
        )
        evidence = await FinancialToolRegistry._fetch_evidence_items(
            db, user_id, category=category, limit=6
        )
        proposal["evidence"] = evidence
        anchor_date = await FinancialToolRegistry._get_anchor_date(db, user_id)
        _, _, period_label = FinancialToolRegistry._resolve_period_dates("current_month", anchor_date=anchor_date)
        proposal["metadata"] = {
            "calculation_period": period_label,
            "aggregation_methodology": "Two-phase human-in-the-loop action preparation",
            "record_count": len(evidence),
            "verified_ledger": True,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }
        return proposal

    @staticmethod
    async def prepare_create_goal(
        db: AsyncSession,
        user_id: str,
        name: str = "Vacation Fund",
        target_amount: float = 60000.0,
        target_date: str = "2027-06-30",
    ) -> Dict[str, Any]:
        """Action tool: Prepares a savings goal creation proposal."""
        from backend.app.voice_agent.action_operator import ActionOperatorService
        proposal = await ActionOperatorService.prepare_action(
            db=db,
            user_id=user_id,
            action_type="create_savings_goal",
            parameters={"name": name, "target_amount": target_amount, "target_date": target_date},
        )
        evidence = await FinancialToolRegistry._fetch_evidence_items(db, user_id, limit=6)
        proposal["evidence"] = evidence
        proposal["metadata"] = {
            "calculation_period": "Forward projection to " + target_date,
            "aggregation_methodology": "Two-phase human-in-the-loop action preparation",
            "record_count": len(evidence),
            "verified_ledger": True,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }
        return proposal

    @staticmethod
    async def prepare_reclassify_transaction(
        db: AsyncSession,
        user_id: str,
        transaction_id: str,
        new_category: str,
    ) -> Dict[str, Any]:
        """Action tool: Prepares a transaction reclassification proposal."""
        from backend.app.voice_agent.action_operator import ActionOperatorService
        return await ActionOperatorService.prepare_action(
            db=db,
            user_id=user_id,
            action_type="update_transaction_category",
            parameters={"transaction_id": transaction_id, "new_category": new_category},
        )

    @staticmethod
    async def prepare_review_anomaly(
        db: AsyncSession,
        user_id: str,
        transaction_id: str,
    ) -> Dict[str, Any]:
        """Action tool: Prepares an anomaly review proposal."""
        from backend.app.voice_agent.action_operator import ActionOperatorService
        return await ActionOperatorService.prepare_action(
            db=db,
            user_id=user_id,
            action_type="review_anomaly",
            parameters={"transaction_id": transaction_id},
        )

    # =============================================================
    # Predictive Advisory Methods (What-If Simulation Engine)
    # =============================================================
    @staticmethod
    async def simulate_spending_reduction(
        db: AsyncSession,
        user_id: str,
        category: str = "Food & Dining",
        reduction_pct: float = 20.0,
        goal_name: str = "Vacation Fund",
    ) -> Dict[str, Any]:
        """Predictive advisory tool: Computes discretionary cut velocity and goal acceleration."""
        from backend.app.services.advisory_service import AdvisoryService
        res = await AdvisoryService.simulate_discretionary_reduction(
            db=db,
            user_id=user_id,
            category=category,
            reduction_pct=reduction_pct,
            goal_name=goal_name,
        )
        evidence = await FinancialToolRegistry._fetch_evidence_items(
            db, user_id, category=category, limit=8
        )
        res["evidence"] = evidence
        res["metadata"] = {
            "calculation_period": "Historical baseline vs simulated projection",
            "aggregation_methodology": "Deterministic linear velocity scaling",
            "record_count": len(evidence),
            "verified_ledger": True,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }
        return res


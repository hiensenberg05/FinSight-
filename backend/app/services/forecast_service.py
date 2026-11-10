import math
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from backend.app.schemas.analytics import ForecastPoint
from backend.app.db.models import Transaction, BankAccount


class ForecastService:
    """
    Predictive Cash-Flow Forecasting Pipeline.
    
    Model: Holt-Winters Double Exponential Smoothing with Linear Trend & Confidence Intervals.
    Input Data: Verified transaction ledger from PostgreSQL (user-scoped, expense kind, grouped by month).
    Output: 12-month historical actuals + 3-month forward projected cash-flow trajectory with 80% confidence bands.
    """

    @staticmethod
    async def get_cashflow_forecast(db: AsyncSession, user_id: str) -> List[ForecastPoint]:
        # 1. Fetch user's current bank balance
        acc_stmt = select(func.coalesce(func.sum(BankAccount.balance_minor), 0)).where(
            and_(BankAccount.user_id == user_id, BankAccount.is_connected == True)
        )
        current_balance_minor = (await db.execute(acc_stmt)).scalar()
        current_balance: Optional[float] = current_balance_minor / 100.0 if current_balance_minor else None

        # 2. Query historical monthly expense totals from verified transactions
        stmt = (
            select(
                func.strftime('%Y-%m', Transaction.transaction_date).label('month_key'),
                func.sum(func.abs(Transaction.amount_minor)).label('total_spent_minor')
            )
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_kind == "expense"
                )
            )
            .group_by('month_key')
            .order_by('month_key')
        )
        rows = (await db.execute(stmt)).all()

        if len(rows) < 3:
            return []

        income_stmt = (
            select(
                func.strftime('%Y-%m', Transaction.transaction_date).label('month_key'),
                func.sum(func.abs(Transaction.amount_minor)).label('total_income_minor'),
            )
            .where(and_(Transaction.user_id == user_id, Transaction.transaction_kind == "income"))
            .group_by('month_key')
            .order_by('month_key')
        )
        income_rows = (await db.execute(income_stmt)).all()
        monthly_income_run_rate = (
            sum(row.total_income_minor for row in income_rows) / len(income_rows) / 100.0
            if income_rows else None
        )

        series = []
        for r in rows:
            val = round(r.total_spent_minor / 100.0, 2)
            series.append((r.month_key, val))

        # Take up to the last 12 historical months
        hist_series = series[-12:]
        y_values = [s[1] for s in hist_series]
        n = len(y_values)

        # 3. Fit Holt-Winters Double Exponential Smoothing (Level + Trend)
        # alpha = 0.35 (level smoothing), beta = 0.15 (trend smoothing)
        alpha = 0.35
        beta = 0.15

        level = [0.0] * n
        trend = [0.0] * n
        fitted = [0.0] * n

        level[0] = y_values[0]
        trend[0] = y_values[1] - y_values[0] if n > 1 else 0.0
        fitted[0] = y_values[0]

        residuals = []
        for t in range(1, n):
            level[t] = alpha * y_values[t] + (1 - alpha) * (level[t - 1] + trend[t - 1])
            trend[t] = beta * (level[t] - level[t - 1]) + (1 - beta) * trend[t - 1]
            fitted[t] = level[t - 1] + trend[t - 1]
            residuals.append(y_values[t] - fitted[t])

        # Residual standard error for confidence interval bounds
        if residuals:
            sigma_e = math.sqrt(sum(r ** 2 for r in residuals) / max(len(residuals), 1))
        else:
            sigma_e = 3200.0

        # Z-score for 80% confidence interval = 1.28
        z_80 = 1.28

        # 4. Construct historical points
        result: List[ForecastPoint] = []
        running_balance = current_balance

        for idx, (m_key, actual_val) in enumerate(hist_series):
            # Parse month name like 'Feb 2024'
            try:
                dt = datetime.strptime(m_key, "%Y-%m")
                display_month = dt.strftime("%b %Y")
            except Exception:
                display_month = m_key

            fit_val = round(fitted[idx], 2)
            half_width = round(z_80 * sigma_e, 2)

            result.append(
                ForecastPoint(
                    date=display_month,
                    month=display_month,
                    actualAmount=actual_val,
                    predictedAmount=fit_val,
                    predictedSpend=fit_val,
                    projectedBalance=None,
                    lowerBound=max(0.0, round(fit_val - half_width, 2)),
                    upperBound=round(fit_val + half_width, 2),
                    upperConfidence=round(fit_val + half_width, 2),
                    lowerConfidence=max(0.0, round(fit_val - half_width, 2)),
                )
            )

        # 5. Project 3 Forward Months (March, April, May 2025)
        last_m_key = hist_series[-1][0]
        try:
            last_dt = datetime.strptime(last_m_key, "%Y-%m")
        except Exception:
            return []

        last_level = level[-1]
        last_trend = trend[-1]

        for step in range(1, 4):
            # Forward step projection: F_{T+h} = L_T + h * b_T
            proj_spend = round(max(0.0, last_level + step * last_trend), 2)
            # Widening confidence band: sigma_h = sigma_e * sqrt(1 + (step-1)*alpha^2)
            step_sigma = sigma_e * math.sqrt(1 + (step - 1) * (alpha ** 2))
            half_width = round(z_80 * step_sigma, 2)

            # Advance month
            proj_month_num = last_dt.month + step
            proj_year = last_dt.year + (proj_month_num - 1) // 12
            proj_month_mod = ((proj_month_num - 1) % 12) + 1
            proj_dt = date(proj_year, proj_month_mod, 1)
            display_month = proj_dt.strftime("%b %Y") + " (Projected)"

            # Update running cash balance trajectory
            if running_balance is not None and monthly_income_run_rate is not None:
                running_balance += monthly_income_run_rate - proj_spend

            result.append(
                ForecastPoint(
                    date=display_month,
                    month=display_month,
                    actualAmount=None,  # No actual for future projection
                    predictedAmount=proj_spend,
                    predictedSpend=proj_spend,
                    projectedBalance=round(running_balance, 2) if running_balance is not None and monthly_income_run_rate is not None else None,
                    lowerBound=max(0.0, round(proj_spend - half_width, 2)),
                    upperBound=round(proj_spend + half_width, 2),
                    upperConfidence=round(proj_spend + half_width, 2),
                    lowerConfidence=max(0.0, round(proj_spend - half_width, 2)),
                )
            )

        return result

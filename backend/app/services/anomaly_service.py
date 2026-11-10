from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from backend.app.db.models import Transaction, Anomaly


class AnomalyService:
    @staticmethod
    async def detect_anomalies(
        db: AsyncSession,
        user_id: str,
        lookback_days: int = 60,
        anchor_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Scan user transactions and identify:
        1. Amounts above configured category thresholds.
        2. Transactions already flagged for review in the ledger.
        """
        if not anchor_date:
            stmt_max = select(func.max(Transaction.transaction_date)).where(Transaction.user_id == user_id)
            max_dt = (await db.execute(stmt_max)).scalar()
            if max_dt:
                if isinstance(max_dt, str):
                    anchor_date = datetime.strptime(max_dt[:10], "%Y-%m-%d").date()
                elif isinstance(max_dt, datetime):
                    anchor_date = max_dt.date()
                elif isinstance(max_dt, date):
                    anchor_date = max_dt
            else:
                anchor_date = date.today()

        cutoff = anchor_date - timedelta(days=max(1, min(int(lookback_days), 3650)))
        stmt = (
            select(Transaction)
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_kind == "expense",
                    Transaction.transaction_date >= cutoff,
                )
            )
            .order_by(Transaction.transaction_date.desc())
        )
        transactions = (await db.execute(stmt)).scalars().all()

        flagged = []
        for tx in transactions:
            amt = tx.amount_minor / 100.0
            is_anomaly = False
            reason = ""

            # Rule 1: High single-ticket purchase in Shopping category
            if tx.category_name == "Shopping" and amt >= 2000:
                is_anomaly = True
                reason = f"Amount exceeds the configured ₹2,000 review threshold for Shopping."

            # Rule 2: Food & Dining spike (> 2.5x typical ₹450-₹600 meal)
            elif tx.category_name in ("Food & Dining", "Food") and amt >= 1400:
                is_anomaly = True
                reason = f"Amount exceeds the configured ₹1,400 review threshold for Food & Dining."

            # Rule 3: Explicit anomaly flag already on record
            elif tx.is_anomaly:
                is_anomaly = True
                reason = tx.anomaly_reason or "Statistically significant spending deviation."

            if is_anomaly:
                tx.is_anomaly = True
                tx.anomaly_reason = reason
                flagged.append({
                    "transaction_id": tx.id,
                    "date": str(tx.transaction_date),
                    "merchant": tx.merchant_name,
                    "category": tx.category_name,
                    "amount": amt,
                    "reason": reason,
                })

        await db.commit()
        return flagged

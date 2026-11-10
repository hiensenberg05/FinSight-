from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from backend.app.api.deps import get_db, get_current_user
from backend.app.db.models import Transaction, User
from backend.app.schemas.transaction import TransactionRead

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=List[TransactionRead])
async def list_transactions(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Transaction).where(Transaction.user_id == user.id)

    if category and category.lower() != "all":
        stmt = stmt.where(Transaction.category_name == category)

    if search:
        search_filter = f"%{search}%"
        stmt = stmt.where(
            or_(
                Transaction.merchant_name.ilike(search_filter),
                Transaction.category_name.ilike(search_filter),
                Transaction.description_original.ilike(search_filter),
            )
        )

    stmt = stmt.order_by(Transaction.transaction_date.desc()).offset(offset).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()

    return [
        TransactionRead(
            id=tx.id,
            date=tx.transaction_date.strftime("%b %d") if tx.transaction_date else "Recent",
            merchant=tx.merchant_name,
            category=tx.category_name,
            amount=tx.amount_minor / 100.0,
            type=tx.transaction_kind,
            channel=tx.payment_mode or "UPI",
            isAnomaly=tx.is_anomaly,
            anomalyReason=tx.anomaly_reason,
        )
        for tx in rows
    ]

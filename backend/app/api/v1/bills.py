from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.api.deps import get_db, get_current_user
from backend.app.db.models import RecurringPayment, User
from backend.app.schemas.bill import BillRead, BillAutoPayUpdate

router = APIRouter(prefix="/bills", tags=["Bills"])


@router.get("", response_model=List[BillRead])
async def list_bills(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(RecurringPayment).where(RecurringPayment.user_id == user.id)
    bills = (await db.execute(stmt)).scalars().all()

    return [
        BillRead(
            id=b.id,
            name=b.name,
            category=b.category_name,
            amount=b.amount_minor / 100.0,
            dueDate=b.due_date_str,
            daysLeft=b.days_left,
            autoPay=b.auto_pay,
            status=b.status,
        )
        for b in bills
    ]


@router.patch("/{bill_id}/autopay")
async def toggle_bill_autopay(
    bill_id: str,
    update: BillAutoPayUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(RecurringPayment).where(
        RecurringPayment.id == bill_id,
        RecurringPayment.user_id == user.id,
    )
    bill = (await db.execute(stmt)).scalars().first()
    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")

    bill.auto_pay = update.autoPay
    await db.commit()
    return {"success": True, "bill_id": bill_id, "autoPay": bill.auto_pay}

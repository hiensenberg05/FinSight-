from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.api.deps import get_db, get_current_user
from backend.app.db.models import BankAccount, User
from backend.app.schemas.account import AccountRead

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get("", response_model=List[AccountRead])
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(BankAccount).where(BankAccount.user_id == user.id)
    accounts = (await db.execute(stmt)).scalars().all()

    return [
        AccountRead(
            id=acc.id,
            name=acc.account_label,
            bankName=acc.institution_name,
            accountNumberMask=acc.account_mask,
            accountType=acc.account_type,
            balance=acc.balance_minor / 100.0,
            currency="₹",
            isConnected=acc.is_connected,
        )
        for acc in accounts
    ]

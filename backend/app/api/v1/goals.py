from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.api.deps import get_db, get_current_user
from backend.app.db.models import SavingsGoal, User
from backend.app.schemas.goal import GoalRead

router = APIRouter(prefix="/goals", tags=["Goals"])


@router.get("", response_model=List[GoalRead])
async def list_goals(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(SavingsGoal).where(SavingsGoal.user_id == user.id)
    goals = (await db.execute(stmt)).scalars().all()

    result = []
    for g in goals:
        target = g.target_amount_minor / 100.0
        current = g.current_amount_minor / 100.0
        pct = int((current / target * 100)) if target > 0 else 0
        result.append(
            GoalRead(
                id=g.id,
                name=g.name,
                currentAmount=current,
                targetAmount=target,
                percentage=pct,
                color=g.color_hex,
            )
        )

    return result

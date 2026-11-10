"""
FinSight Predictive Advisory Simulation API Endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.services.advisory_service import AdvisoryService

router = APIRouter(prefix="/advisory", tags=["Predictive Advisory"])

DEFAULT_USER_ID = "38e0e979-1497-44b6-982e-4039de32327b"


@router.get("/simulate-reduction", summary="Simulate percentage spend reduction in a category")
async def simulate_reduction(
    category: str = Query("Food & Dining", description="Spending category to trim"),
    reduction_pct: float = Query(20.0, ge=0.0, le=100.0, description="Percentage cut"),
    goal_name: Optional[str] = Query("Vacation Fund", description="Target savings goal to accelerate"),
    db: AsyncSession = Depends(get_db),
):
    result = await AdvisoryService.simulate_discretionary_reduction(
        db=db,
        user_id=DEFAULT_USER_ID,
        category=category,
        reduction_pct=reduction_pct,
        goal_name=goal_name,
    )
    return result


@router.get("/predict-overrun", summary="Project month-end budget overrun risk")
async def predict_overrun(
    category: str = Query("Food & Dining", description="Category to evaluate"),
    db: AsyncSession = Depends(get_db),
):
    result = await AdvisoryService.predict_budget_overrun(
        db=db,
        user_id=DEFAULT_USER_ID,
        category=category,
    )
    return result

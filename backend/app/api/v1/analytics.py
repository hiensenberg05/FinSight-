from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_db, get_current_user
from backend.app.db.models import User
from backend.app.services.analytics_service import AnalyticsService
from backend.app.services.forecast_service import ForecastService
from backend.app.schemas.analytics import FinancialHealthMetrics, CategorySpending, ForecastPoint

router = APIRouter(prefix="", tags=["Analytics & Health"])


@router.get("/analytics/health", response_model=FinancialHealthMetrics)
async def get_health_metrics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await AnalyticsService.get_health_metrics(db, user.id)


@router.get("/analytics/categories", response_model=List[CategorySpending])
async def get_category_breakdown(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await AnalyticsService.get_category_spending(db, user.id)


@router.get("/forecasts/cashflow", response_model=List[ForecastPoint])
async def get_cashflow_forecast(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await ForecastService.get_cashflow_forecast(db, user.id)

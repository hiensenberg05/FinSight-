from fastapi import APIRouter
from backend.app.api.v1.accounts import router as accounts_router
from backend.app.api.v1.transactions import router as transactions_router
from backend.app.api.v1.budgets import router as budgets_router
from backend.app.api.v1.goals import router as goals_router
from backend.app.api.v1.bills import router as bills_router
from backend.app.api.v1.analytics import router as analytics_router
from backend.app.api.v1.statements import router as statements_router
from backend.app.api.v1.voice import router as voice_router
from backend.app.api.v1.actions import router as actions_router
from backend.app.api.v1.alerts import router as alerts_router
from backend.app.api.v1.advisory import router as advisory_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(accounts_router)
api_router.include_router(transactions_router)
api_router.include_router(budgets_router)
api_router.include_router(goals_router)
api_router.include_router(bills_router)
api_router.include_router(analytics_router)
api_router.include_router(statements_router)
api_router.include_router(voice_router)
api_router.include_router(actions_router)
api_router.include_router(alerts_router)
api_router.include_router(advisory_router)


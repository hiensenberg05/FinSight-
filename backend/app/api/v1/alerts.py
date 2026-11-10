"""
FinSight Sentinel Proactive Alerts API Endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.services.sentinel_service import SentinelService

router = APIRouter(prefix="/alerts", tags=["Sentinel Alerts"])

DEFAULT_USER_ID = "38e0e979-1497-44b6-982e-4039de32327b"


@router.get("", summary="Get active alerts for user")
async def get_alerts(
    unread_only: bool = Query(False, description="Filter to unread only"),
    limit: int = Query(20, description="Max alerts to return"),
    db: AsyncSession = Depends(get_db),
):
    alerts = await SentinelService.get_user_alerts(
        db=db,
        user_id=DEFAULT_USER_ID,
        unread_only=unread_only,
        limit=limit,
    )
    return {"alerts": alerts, "count": len(alerts)}


@router.post("/check", summary="Trigger Sentinel rule evaluation")
async def trigger_sentinel_check(
    db: AsyncSession = Depends(get_db),
):
    new_alerts = await SentinelService.evaluate_user_rules(
        db=db,
        user_id=DEFAULT_USER_ID,
    )
    return {"new_alerts_created": len(new_alerts), "alerts": new_alerts}


@router.post("/{alert_id}/acknowledge", summary="Acknowledge or dismiss an alert")
async def acknowledge_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
):
    success = await SentinelService.acknowledge_alert(
        db=db,
        alert_id=alert_id,
        user_id=DEFAULT_USER_ID,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"success": True, "alert_id": alert_id}

"""
FinSight Action Operator API Endpoints.
Provides two-phase human-in-the-loop confirmation endpoints for workspace state modifications.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.app.db.session import get_db
from backend.app.db.models import ActionRequest
from backend.app.voice_agent.action_operator import ActionOperatorService

router = APIRouter(prefix="/actions", tags=["Action Operator"])

# Demo default user ID
DEFAULT_USER_ID = "38e0e979-1497-44b6-982e-4039de32327b"


class ActionPrepareRequest(BaseModel):
    action_type: str = Field(..., description="Action type: set_category_budget, create_savings_goal, etc.")
    parameters: Dict[str, Any] = Field(..., description="Action parameters")
    idempotency_key: Optional[str] = Field(None, description="Optional idempotency key")


class ActionExecuteRequest(BaseModel):
    idempotency_key: Optional[str] = Field(None, description="Client idempotency token")


@router.post("/prepare", summary="Phase 1: Prepare proposed action with safety TTL")
async def prepare_action(
    req: ActionPrepareRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        proposal = await ActionOperatorService.prepare_action(
            db=db,
            user_id=DEFAULT_USER_ID,
            action_type=req.action_type,
            parameters=req.parameters,
            idempotency_key=req.idempotency_key,
        )
        return proposal
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{action_id}/confirm", summary="Phase 2: Explicit human-in-the-loop confirmation")
async def confirm_action(
    action_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await ActionOperatorService.execute_action(
        db=db,
        action_id=action_id,
        user_id=DEFAULT_USER_ID,
        actor="user",
    )
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error", "Execution failed"))
    return result


@router.post("/{action_id}/cancel", summary="Cancel a proposed action")
async def cancel_action(
    action_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await ActionOperatorService.cancel_action(
        db=db,
        action_id=action_id,
        user_id=DEFAULT_USER_ID,
    )
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error", "Cancellation failed"))
    return result


@router.get("/pending", summary="List active pending action proposals")
async def get_pending_actions(
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(ActionRequest)
        .where(
            and_(
                ActionRequest.user_id == DEFAULT_USER_ID,
                ActionRequest.status == "pending",
            )
        )
        .order_by(ActionRequest.created_at.desc())
    )
    actions = (await db.execute(stmt)).scalars().all()
    return [
        {
            "action_id": a.id,
            "action_type": a.action_type,
            "description": a.description,
            "target_resource_type": a.target_resource_type,
            "expires_at": a.expires_at.isoformat(),
            "created_at": a.created_at.isoformat(),
        }
        for a in actions
    ]

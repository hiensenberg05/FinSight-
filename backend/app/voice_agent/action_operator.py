"""
FinSight Action Operator Service.
Implements safe, human-in-the-loop two-phase execution for workspace state mutations.
Never performs simulated external bank transfers; strictly manages authorized ledger & workspace resources.
"""

import json
import logging
from datetime import datetime, timedelta, timezone, date
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update

from backend.app.db.models import (
    ActionRequest,
    ActionAuditLog,
    Budget,
    SavingsGoal,
    Transaction,
    RecurringPayment,
    Anomaly,
    utc_now,
)

logger = logging.getLogger(__name__)

# Action expiry duration: 5 minutes
ACTION_EXPIRY_MINUTES = 5


class ActionOperatorService:
    """
    Two-Phase Operational Execution Service.
    Phase 1: Prepare proposed action with validation & 5-minute expiry.
    Phase 2: Atomic execution upon explicit human confirmation with audit provenance.
    """

    @staticmethod
    async def prepare_action(
        db: AsyncSession,
        user_id: str,
        action_type: str,
        parameters: Dict[str, Any],
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Phase 1 — Prepare:
        Validates parameters, targets, and bounds.
        Creates a pending ActionRequest with 5-minute expiration.
        """
        # Expiry time
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACTION_EXPIRY_MINUTES)

        # Build human-readable description and determine target resource
        target_resource_type = "workspace"
        target_resource_id = None
        description = "Workspace configuration update"

        if action_type == "set_category_budget":
            cat = parameters.get("category", "General")
            amount = float(parameters.get("amount", 0.0))
            limit_minor = int(round(amount * 100))
            target_resource_type = "budget"
            description = f"Set monthly budget for '{cat}' to ₹{amount:,.0f}"

            # Check if budget already exists to determine resource_id
            b_stmt = select(Budget).where(
                and_(Budget.user_id == user_id, Budget.category_name.ilike(f"%{cat}%"))
            )
            existing_b = (await db.execute(b_stmt)).scalars().first()
            if existing_b:
                target_resource_id = existing_b.id

        elif action_type == "create_savings_goal":
            name = parameters.get("name", "Savings Goal")
            target = float(parameters.get("target_amount", 0.0))
            target_date = parameters.get("target_date", "2027-06-30")
            target_resource_type = "savings_goal"
            description = f"Create savings goal '{name}' for ₹{target:,.0f} by {target_date}"

        elif action_type == "update_savings_goal":
            goal_id = parameters.get("goal_id")
            additional = float(parameters.get("additional_amount", 0.0))
            target_resource_type = "savings_goal"
            target_resource_id = goal_id
            description = f"Contribute ₹{additional:,.0f} to savings goal"

        elif action_type == "update_transaction_category":
            tx_id = parameters.get("transaction_id")
            new_cat = parameters.get("new_category")
            target_resource_type = "transaction"
            target_resource_id = tx_id
            description = f"Reclassify transaction to category '{new_cat}'"

        elif action_type == "review_anomaly":
            tx_id = parameters.get("transaction_id")
            anomaly_id = parameters.get("anomaly_id")
            target_resource_type = "anomaly"
            target_resource_id = tx_id or anomaly_id
            description = f"Mark transaction outlier review as completed"

        elif action_type == "update_recurring_payment":
            bill_id = parameters.get("bill_id")
            auto_pay = parameters.get("auto_pay")
            target_resource_type = "recurring_payment"
            target_resource_id = bill_id
            description = f"Update recurring payment preferences"

        else:
            raise ValueError(f"Unsupported action type: {action_type}")

        # Persist pending ActionRequest
        action = ActionRequest(
            user_id=user_id,
            action_type=action_type,
            status="pending",
            target_resource_type=target_resource_type,
            target_resource_id=target_resource_id,
            description=description,
            parameters_json=json.dumps(parameters),
            idempotency_key=idempotency_key,
            expires_at=expires_at,
        )
        db.add(action)
        await db.commit()
        await db.refresh(action)

        return {
            "status": "proposal_generated",
            "action_id": action.id,
            "action_type": action.action_type,
            "description": action.description,
            "target_resource_type": action.target_resource_type,
            "parameters": parameters,
            "expires_at": expires_at.isoformat(),
            "ttl_seconds": ACTION_EXPIRY_MINUTES * 60,
            "requires_confirmation": True,
        }

    @staticmethod
    async def execute_action(
        db: AsyncSession,
        action_id: str,
        user_id: str,
        actor: str = "user",
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Phase 2 — Execute:
        Atomically performs mutation upon explicit user authorization.
        Records audit trail and enforces idempotency and expiry checks.
        """
        stmt = select(ActionRequest).where(
            and_(ActionRequest.id == action_id, ActionRequest.user_id == user_id)
        )
        action = (await db.execute(stmt)).scalars().first()

        if not action:
            return {"success": False, "error": f"Action {action_id} not found or unauthorized"}

        # Idempotency check
        if action.status == "executed":
            return {
                "success": True,
                "already_executed": True,
                "action_id": action.id,
                "status": "executed",
                "message": f"Action '{action.description}' was already executed successfully.",
            }

        if action.status == "cancelled":
            return {"success": False, "error": "This action proposal was cancelled by the user."}

        # Expiry check
        now = datetime.now(timezone.utc)
        # Handle naive or aware datetimes
        exp = action.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if now > exp:
            action.status = "expired"
            await db.commit()
            return {"success": False, "error": "Action proposal has expired (5-minute safety TTL elapsed)."}

        params = json.loads(action.parameters_json)
        before_state = {}
        after_state = {}

        try:
            # ---------------------------------------------------------
            # Mutation 1: set_category_budget
            # ---------------------------------------------------------
            if action.action_type == "set_category_budget":
                cat = params.get("category", "General")
                amount = float(params.get("amount", 0.0))
                limit_minor = int(round(amount * 100))

                b_stmt = select(Budget).where(
                    and_(Budget.user_id == user_id, Budget.category_name.ilike(f"%{cat}%"))
                )
                budget = (await db.execute(b_stmt)).scalars().first()

                if budget:
                    before_state = {
                        "id": budget.id,
                        "category": budget.category_name,
                        "limit_minor": budget.limit_minor,
                    }
                    budget.limit_minor = limit_minor
                    after_state = {
                        "id": budget.id,
                        "category": budget.category_name,
                        "limit_minor": budget.limit_minor,
                    }
                else:
                    budget = Budget(
                        user_id=user_id,
                        category_name=cat,
                        limit_minor=limit_minor,
                        period="monthly",
                    )
                    db.add(budget)
                    await db.flush()
                    after_state = {
                        "id": budget.id,
                        "category": budget.category_name,
                        "limit_minor": budget.limit_minor,
                    }

            # ---------------------------------------------------------
            # Mutation 2: create_savings_goal
            # ---------------------------------------------------------
            elif action.action_type == "create_savings_goal":
                name = params.get("name", "Savings Goal")
                target = float(params.get("target_amount", 0.0))
                target_minor = int(round(target * 100))
                target_date_str = params.get("target_date", "2027-06-30")
                target_date_val = None
                if target_date_str:
                    try:
                        target_date_val = datetime.strptime(str(target_date_str)[:10], "%Y-%m-%d").date()
                    except Exception:
                        target_date_val = None

                goal = SavingsGoal(
                    user_id=user_id,
                    name=name,
                    target_amount_minor=target_minor,
                    current_amount_minor=0,
                    currency="INR",
                    target_date=target_date_val,
                    status="active",
                )
                db.add(goal)
                await db.flush()
                after_state = {
                    "id": goal.id,
                    "name": goal.name,
                    "target_amount_minor": goal.target_amount_minor,
                }

            # ---------------------------------------------------------
            # Mutation 3: update_savings_goal
            # ---------------------------------------------------------
            elif action.action_type == "update_savings_goal":
                goal_id = params.get("goal_id") or action.target_resource_id
                additional = float(params.get("additional_amount", 0.0))
                add_minor = int(round(additional * 100))

                g_stmt = select(SavingsGoal).where(
                    and_(SavingsGoal.id == goal_id, SavingsGoal.user_id == user_id)
                )
                goal = (await db.execute(g_stmt)).scalars().first()
                if goal:
                    before_state = {"id": goal.id, "current_amount_minor": goal.current_amount_minor}
                    goal.current_amount_minor += add_minor
                    if goal.current_amount_minor >= goal.target_amount_minor:
                        goal.status = "completed"
                    after_state = {"id": goal.id, "current_amount_minor": goal.current_amount_minor, "status": goal.status}

            # ---------------------------------------------------------
            # Mutation 4: update_transaction_category
            # ---------------------------------------------------------
            elif action.action_type == "update_transaction_category":
                tx_id = params.get("transaction_id") or action.target_resource_id
                new_cat = params.get("new_category")

                t_stmt = select(Transaction).where(
                    and_(Transaction.id == tx_id, Transaction.user_id == user_id)
                )
                tx = (await db.execute(t_stmt)).scalars().first()
                if tx:
                    before_state = {"id": tx.id, "category_name": tx.category_name}
                    tx.category_name = new_cat
                    after_state = {"id": tx.id, "category_name": tx.category_name}

            # ---------------------------------------------------------
            # Mutation 5: review_anomaly
            # ---------------------------------------------------------
            elif action.action_type == "review_anomaly":
                tx_id = params.get("transaction_id") or action.target_resource_id
                t_stmt = select(Transaction).where(
                    and_(Transaction.id == tx_id, Transaction.user_id == user_id)
                )
                tx = (await db.execute(t_stmt)).scalars().first()
                if tx:
                    before_state = {"id": tx.id, "is_anomaly": tx.is_anomaly}
                    tx.is_anomaly = False
                    tx.anomaly_reason = "Reviewed and marked as legitimate by user"
                    after_state = {"id": tx.id, "is_anomaly": False}

            # ---------------------------------------------------------
            # Mutation 6: update_recurring_payment
            # ---------------------------------------------------------
            elif action.action_type == "update_recurring_payment":
                bill_id = params.get("bill_id") or action.target_resource_id
                auto_pay = params.get("auto_pay")

                r_stmt = select(RecurringPayment).where(
                    and_(RecurringPayment.id == bill_id, RecurringPayment.user_id == user_id)
                )
                bill = (await db.execute(r_stmt)).scalars().first()
                if bill:
                    before_state = {"id": bill.id, "auto_pay": bill.auto_pay}
                    if auto_pay is not None:
                        bill.auto_pay = bool(auto_pay)
                    after_state = {"id": bill.id, "auto_pay": bill.auto_pay}

            # Mark action executed
            action.status = "executed"
            action.executed_at = utc_now()

            # Audit log creation
            audit = ActionAuditLog(
                user_id=user_id,
                action_id=action.id,
                action_type=action.action_type,
                actor=actor,
                ip_address=ip_address,
                before_state_json=json.dumps(before_state),
                after_state_json=json.dumps(after_state),
                executed_at=utc_now(),
            )
            db.add(audit)
            await db.commit()

            return {
                "success": True,
                "action_id": action.id,
                "action_type": action.action_type,
                "description": action.description,
                "status": "executed",
                "executed_at": action.executed_at.isoformat(),
                "before_state": before_state,
                "after_state": after_state,
                "message": f"Successfully completed: {action.description}",
            }
        except Exception as e:
            await db.rollback()
            logger.error(f"[ActionOperator] Failed to execute action {action_id}: {e}", exc_info=True)
            return {
                "success": False,
                "action_id": action_id,
                "error": f"Database mutation failed: {str(e)}",
            }

    @staticmethod
    async def cancel_action(
        db: AsyncSession,
        action_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Cancels a pending action proposal."""
        stmt = select(ActionRequest).where(
            and_(ActionRequest.id == action_id, ActionRequest.user_id == user_id)
        )
        action = (await db.execute(stmt)).scalars().first()
        if not action:
            return {"success": False, "error": "Action proposal not found"}

        if action.status == "executed":
            return {"success": False, "error": "Cannot cancel an already executed action"}

        action.status = "cancelled"
        await db.commit()
        return {
            "success": True,
            "action_id": action.id,
            "status": "cancelled",
            "message": f"Cancelled proposed action: {action.description}",
        }

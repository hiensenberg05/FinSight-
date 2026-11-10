"""
Test suite for FinSight Operational Services:
- Action Operator Service (Two-phase safe execution, idempotency, audit logs)
- Real-Time Sentinel Service (Deterministic rule evaluation, threshold alerts)
- Predictive Advisory Service (What-if simulations and budget overrun projections)
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import select

from backend.app.db.session import async_session_maker
from backend.app.voice_agent.action_operator import ActionOperatorService
from backend.app.services.sentinel_service import SentinelService
from backend.app.services.advisory_service import AdvisoryService
from backend.app.db.models import Budget, SavingsGoal, ActionRequest, ActionAuditLog, FinancialAlert

TEST_USER_ID = "38e0e979-1497-44b6-982e-4039de32327b"


@pytest.mark.asyncio
async def test_action_operator_two_phase_budget():
    """Test Phase 1 (Prepare) -> Phase 2 (Execute) for category budget."""
    async with async_session_maker() as session:
        # Phase 1: Prepare
        proposal = await ActionOperatorService.prepare_action(
            db=session,
            user_id=TEST_USER_ID,
            action_type="set_category_budget",
            parameters={"category": "Food & Dining", "amount": 15000.0},
        )
        assert proposal["status"] == "proposal_generated"
        assert proposal["requires_confirmation"] is True
        action_id = proposal["action_id"]

        # Verify pending action in DB
        action = (await session.execute(select(ActionRequest).where(ActionRequest.id == action_id))).scalars().first()
        assert action is not None
        assert action.status == "pending"

        # Phase 2: Execute
        exec_res = await ActionOperatorService.execute_action(
            db=session,
            action_id=action_id,
            user_id=TEST_USER_ID,
            actor="user",
        )
        assert exec_res["success"] is True
        assert exec_res["status"] == "executed"

        # Verify Budget was updated in DB
        b_stmt = select(Budget).where(Budget.user_id == TEST_USER_ID, Budget.category_name.ilike("%Food%"))
        budget = (await session.execute(b_stmt)).scalars().first()
        assert budget is not None
        assert budget.limit_minor == 1500000  # ₹15,000 in paise

        # Verify Audit Log
        audit_stmt = select(ActionAuditLog).where(ActionAuditLog.action_id == action_id)
        audit = (await session.execute(audit_stmt)).scalars().first()
        assert audit is not None
        assert audit.action_type == "set_category_budget"

        # Verify Idempotency: executing again returns already_executed
        idempotent_res = await ActionOperatorService.execute_action(
            db=session,
            action_id=action_id,
            user_id=TEST_USER_ID,
        )
        assert idempotent_res["success"] is True
        assert idempotent_res.get("already_executed") is True


@pytest.mark.asyncio
async def test_action_operator_cancellation():
    """Test cancelling an action proposal."""
    async with async_session_maker() as session:
        proposal = await ActionOperatorService.prepare_action(
            db=session,
            user_id=TEST_USER_ID,
            action_type="create_savings_goal",
            parameters={"name": "Emergency Fund", "target_amount": 50000.0, "target_date": "2027-12-31"},
        )
        action_id = proposal["action_id"]

        cancel_res = await ActionOperatorService.cancel_action(session, action_id, TEST_USER_ID)
        assert cancel_res["success"] is True
        assert cancel_res["status"] == "cancelled"

        # Executing cancelled action must fail
        fail_res = await ActionOperatorService.execute_action(session, action_id, TEST_USER_ID)
        assert fail_res["success"] is False
        assert "cancelled" in fail_res["error"]


@pytest.mark.asyncio
async def test_sentinel_rule_evaluation():
    """Test Sentinel Service detects threshold breaches and upcoming bills."""
    async with async_session_maker() as session:
        alerts = await SentinelService.evaluate_user_rules(session, TEST_USER_ID)
        assert isinstance(alerts, list)

        # Fetch alerts for user
        all_alerts = await SentinelService.get_user_alerts(session, TEST_USER_ID)
        assert len(all_alerts) >= 1

        # Check alert structure
        first_alert = all_alerts[0]
        assert "id" in first_alert
        assert "severity" in first_alert
        assert "title" in first_alert
        assert "detail" in first_alert

        # Acknowledge alert
        ack_res = await SentinelService.acknowledge_alert(session, first_alert["id"], TEST_USER_ID)
        assert ack_res is True


@pytest.mark.asyncio
async def test_advisory_what_if_simulation():
    """Test Predictive Advisory discretionary cut calculation."""
    async with async_session_maker() as session:
        res = await AdvisoryService.simulate_discretionary_reduction(
            db=session,
            user_id=TEST_USER_ID,
            category="Food & Dining",
            reduction_pct=20.0,
            goal_name="Vacation Fund",
        )
        if res.get("status") == "insufficient_history":
            assert res["historical_monthly_spend"] is None
            assert res["category"] == "Food & Dining"
        else:
            assert res["simulation_type"] == "discretionary_reduction"
            assert res["reduction_percentage"] == 20.0
            assert res["monthly_savings"] > 0
            assert res["annualized_savings"] == round(res["monthly_savings"] * 12.0, 2)
            assert "goal_impact" in res
            assert "slider_bounds" in res


@pytest.mark.asyncio
async def test_advisory_budget_overrun():
    """Test Predictive Advisory budget overrun run-rate."""
    async with async_session_maker() as session:
        res = await AdvisoryService.predict_budget_overrun(
            db=session,
            user_id=TEST_USER_ID,
            category="Food & Dining",
        )
        assert "budget_limit" in res
        assert "projected_month_end_spend" in res
        assert "daily_run_rate" in res

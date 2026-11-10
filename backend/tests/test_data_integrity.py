"""
Automated Pytest for Data Integrity, Invariants, and Multi-Tenant Isolation.
"""

import pytest
from sqlalchemy import select, func
from backend.app.db.session import async_session_maker
from backend.app.db.models import (
    User, BankAccount, Transaction, TransactionLink, Budget, SavingsGoal, Anomaly
)


@pytest.mark.asyncio
async def test_production_data_volumes():
    async with async_session_maker() as session:
        users_count = await session.scalar(select(func.count(User.id)))
        acc_count = await session.scalar(select(func.count(BankAccount.id)))
        txns_count = await session.scalar(select(func.count(Transaction.id)))
        anom_count = await session.scalar(select(func.count(Anomaly.id)))

        assert users_count == 20, f"Expected 20 users, got {users_count}"
        assert acc_count >= 30, f"Expected >= 30 accounts, got {acc_count}"
        assert txns_count >= 15000, f"Expected >= 15000 transactions, got {txns_count}"
        assert anom_count >= 200, f"Expected >= 200 anomalies, got {anom_count}"


@pytest.mark.asyncio
async def test_exact_integer_paise_no_nulls_or_floats():
    async with async_session_maker() as session:
        null_count = await session.scalar(
            select(func.count(Transaction.id)).where(Transaction.amount_minor == None)
        )
        zero_count = await session.scalar(
            select(func.count(Transaction.id)).where(Transaction.amount_minor == 0)
        )
        assert null_count == 0
        assert zero_count == 0


@pytest.mark.asyncio
async def test_zero_orphan_records():
    async with async_session_maker() as session:
        orphan_accs = await session.scalar(
            select(func.count(BankAccount.id)).where(BankAccount.user_id.not_in(select(User.id)))
        )
        orphan_txns = await session.scalar(
            select(func.count(Transaction.id)).where(Transaction.user_id.not_in(select(User.id)))
        )
        orphan_txn_accs = await session.scalar(
            select(func.count(Transaction.id)).where(Transaction.account_id.not_in(select(BankAccount.id)))
        )
        orphan_anoms = await session.scalar(
            select(func.count(Anomaly.id)).where(Anomaly.transaction_id.not_in(select(Transaction.id)))
        )

        assert orphan_accs == 0
        assert orphan_txns == 0
        assert orphan_txn_accs == 0
        assert orphan_anoms == 0


@pytest.mark.asyncio
async def test_cross_tenant_isolation():
    async with async_session_maker() as session:
        leaks = await session.scalar(
            select(func.count(Transaction.id))
            .join(BankAccount, Transaction.account_id == BankAccount.id)
            .where(Transaction.user_id != BankAccount.user_id)
        )
        assert leaks == 0


@pytest.mark.asyncio
async def test_internal_transfer_reconciliation():
    async with async_session_maker() as session:
        pairs = (await session.execute(
            select(TransactionLink.from_transaction_id, TransactionLink.to_transaction_id)
            .where(TransactionLink.link_type == "transfer_pair")
        )).all()

        assert len(pairs) > 0, "Expected generated transfer pairs"
        for from_id, to_id in pairs:
            from_t = await session.get(Transaction, from_id)
            to_t = await session.get(Transaction, to_id)
            assert from_t is not None
            assert to_t is not None
            assert from_t.amount_minor + to_t.amount_minor == 0, "Transfer pair does not balance to zero!"

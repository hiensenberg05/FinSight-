"""
FinSight Relational Data Integrity and Financial Invariant Verification Script.
Conforms to data_schema.md Section 2 and Section 12.9.
"""

import asyncio
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy import select, func
from backend.app.db.session import async_session_maker
from backend.app.db.models import (
    User, BankAccount, Category, Merchant,
    Transaction, TransactionLink, Budget, SavingsGoal, RecurringPayment, Anomaly
)


async def run_integrity_verification():
    print("=" * 60)
    print("FINSIGHT DATA INTEGRITY & FINANCIAL INVARIANT VERIFICATION")
    print("=" * 60)

    async with async_session_maker() as session:
        # 1. Row Count Audits
        users_count = await session.scalar(select(func.count(User.id)))
        acc_count = await session.scalar(select(func.count(BankAccount.id)))
        txns_count = await session.scalar(select(func.count(Transaction.id)))
        budgets_count = await session.scalar(select(func.count(Budget.id)))
        goals_count = await session.scalar(select(func.count(SavingsGoal.id)))
        bills_count = await session.scalar(select(func.count(RecurringPayment.id)))
        anom_count = await session.scalar(select(func.count(Anomaly.id)))
        links_count = await session.scalar(select(func.count(TransactionLink.id)))

        print(f"[1] Entity Counts in Database:")
        print(f"    Users: {users_count}")
        print(f"    Bank Accounts: {acc_count}")
        print(f"    Transactions: {txns_count}")
        print(f"    Budgets: {budgets_count}")
        print(f"    Savings Goals: {goals_count}")
        print(f"    Recurring Payments: {bills_count}")
        print(f"    Anomalies: {anom_count}")
        print(f"    Transaction Links: {links_count}")

        assert users_count == 20, f"Expected 20 users, found {users_count}"
        assert txns_count >= 15000, f"Expected >= 15000 transactions, found {txns_count}"
        assert anom_count >= 200, f"Expected >= 200 anomalies, found {anom_count}"
        print("    --> PASS: Volume thresholds meet production schema spec.")

        # 2. Integer Minor Units & Non-zero Invariant
        non_integer_txns = await session.scalar(
            select(func.count(Transaction.id)).where(Transaction.amount_minor == None)
        )
        zero_amount_txns = await session.scalar(
            select(func.count(Transaction.id)).where(Transaction.amount_minor == 0)
        )
        assert non_integer_txns == 0, "Found NULL amount_minor!"
        assert zero_amount_txns == 0, "Found zero amount_minor violating chk_nonzero_amount!"
        print("[2] Monetary Representation Check:")
        print("    --> PASS: 100% of transactions use integer paise (no nulls, no floats, no zero amounts).")

        # 3. Referential Integrity (No Orphan Rows)
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
        assert orphan_accs == 0, f"Found {orphan_accs} orphan accounts"
        assert orphan_txns == 0, f"Found {orphan_txns} orphan transactions"
        assert orphan_txn_accs == 0, f"Found {orphan_txn_accs} transactions with non-existent accounts"
        assert orphan_anoms == 0, f"Found {orphan_anoms} anomalies with non-existent transactions"
        print("[3] Referential Integrity Audit:")
        print("    --> PASS: Zero orphan records across accounts, transactions, and anomalies.")

        # 4. Multi-Tenant Cross-User Isolation
        # Verify that for any user, all their transactions belong only to their own accounts
        misplaced_txns = await session.scalar(
            select(func.count(Transaction.id))
            .join(BankAccount, Transaction.account_id == BankAccount.id)
            .where(Transaction.user_id != BankAccount.user_id)
        )
        assert misplaced_txns == 0, f"Detected {misplaced_txns} cross-user account/transaction leaks!"
        print("[4] Tenancy Boundary Isolation:")
        print("    --> PASS: Complete tenant isolation; 0 cross-user data leakage.")

        # 5. Double-Entry Transfer Invariant
        transfer_links = (await session.execute(
            select(TransactionLink.from_transaction_id, TransactionLink.to_transaction_id)
            .where(TransactionLink.link_type == "transfer_pair")
        )).all()

        reconciliation_failures = 0
        for from_id, to_id in transfer_links:
            from_txn = await session.get(Transaction, from_id)
            to_txn = await session.get(Transaction, to_id)
            if from_txn and to_txn:
                # Sum of signed paise in a transfer pair must be exactly 0
                if from_txn.amount_minor + to_txn.amount_minor != 0:
                    reconciliation_failures += 1

        assert reconciliation_failures == 0, f"Found {reconciliation_failures} un-reconciled transfer pairs!"
        print(f"[5] Internal Transfer Zero-Sum Invariant:")
        print(f"    --> PASS: Audited {len(transfer_links)} transfer pairs: all sum to exactly 0 paise.")

        print("=" * 60)
        print("ALL DATA INTEGRITY AND INVARIANT CHECKS PASSED (100%)")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_integrity_verification())

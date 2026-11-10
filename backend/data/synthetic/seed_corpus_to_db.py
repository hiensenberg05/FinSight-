"""
FinSight Database Seeder from Canonical Synthetic Corpus.
Loads canonical datasets from backend/data/synthetic/corpus/ into PostgreSQL or SQLite.
"""

import asyncio
import csv
import os
from datetime import datetime, date
from sqlalchemy import select, delete, func
from backend.app.db.session import async_session_maker, init_db
from backend.app.db.models import (
    User, BankAccount, Category, Merchant, MerchantAlias,
    Transaction, TransactionLink, Budget, SavingsGoal, RecurringPayment, Anomaly
)

CORPUS_DIR = os.path.join(os.path.dirname(__file__), "corpus")

async def seed_from_corpus(primary_only: bool = False):
    print(f"Initializing database tables...")
    await init_db()

    async with async_session_maker() as session:
        # Load Users
        users_file = os.path.join(CORPUS_DIR, "users.csv")
        with open(users_file, "r", encoding="utf-8") as f:
            user_rows = list(csv.DictReader(f))

        if primary_only:
            user_rows = [u for u in user_rows if u.get("is_primary_demo") == "True"]

        user_ids = {u["id"] for u in user_rows}
        print(f"Loading {len(user_rows)} users...")
        for u in user_rows:
            existing = await session.get(User, u["id"])
            if not existing:
                session.add(User(
                    id=u["id"],
                    email=u["email"],
                    password_hash=u["password_hash"],
                    display_name=u["display_name"],
                    preferred_language=u["preferred_language"],
                    base_currency=u["base_currency"],
                    persona_type=u["persona_type"],
                    is_active=(u["is_active"] == "True")
                ))
        await session.commit()

        # Load Categories
        cats_file = os.path.join(CORPUS_DIR, "categories.csv")
        with open(cats_file, "r", encoding="utf-8") as f:
            cat_rows = list(csv.DictReader(f))
        print(f"Loading {len(cat_rows)} categories...")
        for c in cat_rows:
            res = await session.execute(select(Category).where(Category.slug == c["slug"]))
            if not res.scalar_one_or_none():
                session.add(Category(
                    name=c["name"],
                    slug=c["slug"],
                    category_type=c["type"],
                    color_hex=c["color"],
                    is_system=True
                ))
        await session.commit()

        # Load Bank Accounts
        acc_file = os.path.join(CORPUS_DIR, "bank_accounts.csv")
        with open(acc_file, "r", encoding="utf-8") as f:
            acc_rows = [a for a in csv.DictReader(f) if a["user_id"] in user_ids]
        print(f"Loading {len(acc_rows)} bank accounts...")
        for a in acc_rows:
            existing = await session.get(BankAccount, a["id"])
            if not existing:
                session.add(BankAccount(
                    id=a["id"],
                    user_id=a["user_id"],
                    institution_name=a["institution_name"],
                    account_label=a["account_label"],
                    account_type=a["account_type"],
                    account_mask=a["account_mask"],
                    currency=a["currency"],
                    balance_minor=int(a["balance_minor"]),
                    is_connected=(a["is_connected"] == "True")
                ))
        await session.commit()

        # Load Budgets
        budgets_file = os.path.join(CORPUS_DIR, "budgets.csv")
        with open(budgets_file, "r", encoding="utf-8") as f:
            b_rows = [b for b in csv.DictReader(f) if b["user_id"] in user_ids]
        print(f"Loading {len(b_rows)} budgets...")
        for b in b_rows:
            existing = await session.get(Budget, b["id"])
            if not existing:
                session.add(Budget(
                    id=b["id"],
                    user_id=b["user_id"],
                    category_name=b["category_name"],
                    limit_minor=int(b["limit_minor"]),
                    period=b["period"],
                    alert_threshold_pct=float(b["alert_threshold_pct"])
                ))
        await session.commit()

        # Load Savings Goals
        goals_file = os.path.join(CORPUS_DIR, "savings_goals.csv")
        with open(goals_file, "r", encoding="utf-8") as f:
            g_rows = [g for g in csv.DictReader(f) if g["user_id"] in user_ids]
        print(f"Loading {len(g_rows)} savings goals...")
        for g in g_rows:
            existing = await session.get(SavingsGoal, g["id"])
            if not existing:
                session.add(SavingsGoal(
                    id=g["id"],
                    user_id=g["user_id"],
                    name=g["name"],
                    target_amount_minor=int(g["target_amount_minor"]),
                    current_amount_minor=int(g["current_amount_minor"]),
                    currency=g["currency"],
                    color_hex=g["color_hex"],
                    target_date=date.fromisoformat(g["target_date"]) if g.get("target_date") else None,
                    status=g["status"]
                ))
        await session.commit()

        # Load Recurring Payments
        bills_file = os.path.join(CORPUS_DIR, "recurring_payments.csv")
        with open(bills_file, "r", encoding="utf-8") as f:
            bill_rows = [r for r in csv.DictReader(f) if r["user_id"] in user_ids]
        print(f"Loading {len(bill_rows)} recurring payments...")
        for r in bill_rows:
            existing = await session.get(RecurringPayment, r["id"])
            if not existing:
                session.add(RecurringPayment(
                    id=r["id"],
                    user_id=r["user_id"],
                    name=r["name"],
                    category_name=r["category_name"],
                    amount_minor=int(r["amount_minor"]),
                    currency=r["currency"],
                    due_date_str=r["due_date_str"],
                    days_left=int(r["days_left"]),
                    auto_pay=(r["auto_pay"] == "True"),
                    status=r["status"]
                ))
        await session.commit()

        # Load Transactions in Batches (if not already loaded)
        existing_txns_count = await session.scalar(select(func.count(Transaction.id)))
        if existing_txns_count == 0:
            txns_file = os.path.join(CORPUS_DIR, "transactions.csv")
            with open(txns_file, "r", encoding="utf-8") as f:
                txn_rows = [t for t in csv.DictReader(f) if t["user_id"] in user_ids]
            print(f"Loading {len(txn_rows)} transactions in batches...")

            batch = []
            for idx, t in enumerate(txn_rows):
                batch.append(Transaction(
                    id=t["id"],
                    user_id=t["user_id"],
                    account_id=t["account_id"],
                    transaction_date=date.fromisoformat(t["transaction_date"]),
                    merchant_name=t["merchant_name"],
                    category_name=t["category_name"],
                    amount_minor=int(t["amount_minor"]),
                    currency=t["currency"],
                    transaction_kind=t["transaction_kind"],
                    payment_mode=t["payment_mode"],
                    description_original=t["description_original"],
                    is_internal_transfer=(t["is_internal_transfer"] == "True"),
                    is_anomaly=(t["is_anomaly"] == "True"),
                    anomaly_reason=t["anomaly_reason"] if t["anomaly_reason"] else None
                ))
                if len(batch) >= 1000:
                    session.add_all(batch)
                    await session.commit()
                    batch = []
            if batch:
                session.add_all(batch)
                await session.commit()
        else:
            print(f"Transactions already loaded ({existing_txns_count} rows), skipping.")

        # Load Anomalies
        existing_anom_count = await session.scalar(select(func.count(Anomaly.id)))
        if existing_anom_count == 0:
            anomalies_file = os.path.join(CORPUS_DIR, "anomaly_ground_truth.csv")
            with open(anomalies_file, "r", encoding="utf-8") as f:
                anom_rows = [a for a in csv.DictReader(f) if a["user_id"] in user_ids]
            print(f"Loading {len(anom_rows)} anomalies...")
            for a in anom_rows:
                session.add(Anomaly(
                    id=a["id"],
                    user_id=a["user_id"],
                    transaction_id=a["transaction_id"],
                    anomaly_type=a["anomaly_type"],
                    severity=a["severity"],
                    score=float(a["score"]),
                    reason=a["reason"],
                    status=a["status"]
                ))
            await session.commit()
        else:
            print(f"Anomalies already loaded ({existing_anom_count} rows), skipping.")

        # Load Transaction Links
        existing_links_count = await session.scalar(select(func.count(TransactionLink.id)))
        if existing_links_count == 0:
            links_file = os.path.join(CORPUS_DIR, "transaction_links.csv")
            if os.path.exists(links_file):
                with open(links_file, "r", encoding="utf-8") as f:
                    link_rows = [l for l in csv.DictReader(f) if l["user_id"] in user_ids]
                print(f"Loading {len(link_rows)} transaction links...")
                for l in link_rows:
                    session.add(TransactionLink(
                        id=l["id"],
                        user_id=l["user_id"],
                        from_transaction_id=l["from_transaction_id"],
                        to_transaction_id=l["to_transaction_id"],
                        link_type=l["link_type"]
                    ))
                await session.commit()
        else:
            print(f"Transaction links already loaded ({existing_links_count} rows), skipping.")

    print(f"Seeding completed successfully!")

if __name__ == "__main__":
    import sys
    primary_only_flag = "--primary-only" in sys.argv
    asyncio.run(seed_from_corpus(primary_only=primary_only_flag))

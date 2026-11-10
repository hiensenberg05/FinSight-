import logging
from datetime import date, timedelta
from sqlalchemy import select
from backend.app.db.session import async_session_maker
from backend.app.db.models import (
    User,
    BankAccount,
    Budget,
    SavingsGoal,
    RecurringPayment,
    Transaction,
    Anomaly,
)

logger = logging.getLogger(__name__)


async def seed_demo_persona():
    """
    Seed Aarav Mehta persona matching the frontend specifications and hackathon demo requirements.
    """
    async with async_session_maker() as db:
        # Check if already seeded
        stmt = select(User).where(User.email == "aarav.mehta@example.com")
        existing_user = (await db.execute(stmt)).scalars().first()
        if existing_user:
            logger.info("[Seed] Demo user Aarav Mehta already exists. Skipping seed.")
            return

        logger.info("[Seed] Seeding Aarav Mehta demo persona...")

        # 1. User
        user = User(
            email="aarav.mehta@example.com",
            password_hash="pbkdf2$mock$hash",
            display_name="Aarav Mehta",
            preferred_language="en",
            base_currency="INR",
        )
        db.add(user)
        await db.flush()

        # 2. Bank Accounts
        acc_hdfc = BankAccount(
            user_id=user.id,
            institution_name="HDFC Bank",
            account_label="Everyday account",
            account_type="checking",
            account_mask="4821",
            currency="INR",
            balance_minor=9825000,  # ₹98,250.00
            is_connected=True,
        )
        acc_sbi = BankAccount(
            user_id=user.id,
            institution_name="SBI Bank",
            account_label="High-yield savings",
            account_type="savings",
            account_mask="9034",
            currency="INR",
            balance_minor=2625050,  # ₹26,250.50
            is_connected=True,
        )
        db.add_all([acc_hdfc, acc_sbi])
        await db.flush()

        # 3. Budgets
        budgets = [
            Budget(user_id=user.id, category_name="Food & Dining", limit_minor=1800000, period="Feb 2025"),
            Budget(user_id=user.id, category_name="Bills & Utilities", limit_minor=1200000, period="Feb 2025"),
            Budget(user_id=user.id, category_name="Travel & transport", limit_minor=800000, period="Feb 2025"),
            Budget(user_id=user.id, category_name="Shopping", limit_minor=750000, period="Feb 2025"),
        ]
        db.add_all(budgets)

        # 4. Savings Goals
        goals = [
            SavingsGoal(
                user_id=user.id,
                name="Vacation Fund",
                target_amount_minor=6000000,
                current_amount_minor=3600000,
                color_hex="#06B6D4",
                status="active",
            ),
            SavingsGoal(
                user_id=user.id,
                name="Emergency Fund",
                target_amount_minor=10000000,
                current_amount_minor=8500000,
                color_hex="#EC4899",
                status="active",
            ),
        ]
        db.add_all(goals)

        # 5. Recurring Payments (Bills)
        bills = [
            RecurringPayment(
                user_id=user.id,
                name="Netflix Premium 4K",
                category_name="Subscription",
                amount_minor=64900,
                due_date_str="Feb 10, 2025",
                days_left=4,
                auto_pay=True,
                status="due_soon",
            ),
            RecurringPayment(
                user_id=user.id,
                name="ACT Fibernet 300 Mbps",
                category_name="Broadband",
                amount_minor=105000,
                due_date_str="Feb 14, 2025",
                days_left=8,
                auto_pay=True,
                status="scheduled",
            ),
            RecurringPayment(
                user_id=user.id,
                name="BESCOM Electricity Bill",
                category_name="Utilities",
                amount_minor=145000,
                due_date_str="Feb 20, 2025",
                days_left=14,
                auto_pay=False,
                status="scheduled",
            ),
            RecurringPayment(
                user_id=user.id,
                name="Apartment Maintenance & Rent",
                category_name="Housing",
                amount_minor=1800000,
                due_date_str="Mar 01, 2025",
                days_left=23,
                auto_pay=False,
                status="scheduled",
            ),
        ]
        db.add_all(bills)

        # 6. Historical Transactions (Recent + Anomalies + Past months)
        txs = [
            Transaction(
                user_id=user.id,
                account_id=acc_hdfc.id,
                transaction_date=date(2025, 2, 3),
                merchant_name="Uber",
                category_name="Transportation",
                amount_minor=35000,
                transaction_kind="expense",
                payment_mode="UPI",
                description_original="UPI/UBER/309230/RIDE",
            ),
            Transaction(
                user_id=user.id,
                account_id=acc_hdfc.id,
                transaction_date=date(2025, 2, 2),
                merchant_name="Netflix",
                category_name="Subscriptions",
                amount_minor=64900,
                transaction_kind="expense",
                payment_mode="Card",
                description_original="CARD/NETFLIX.COM/MONTHLY",
            ),
            Transaction(
                user_id=user.id,
                account_id=acc_hdfc.id,
                transaction_date=date(2025, 2, 2),
                merchant_name="Swiggy",
                category_name="Food & Dining",
                amount_minor=148000,
                transaction_kind="expense",
                payment_mode="UPI",
                description_original="UPI/SWIGGY/940294/DINNER",
                is_anomaly=True,
                anomaly_reason="3.2x higher than typical weekend dinner orders",
            ),
            Transaction(
                user_id=user.id,
                account_id=acc_hdfc.id,
                transaction_date=date(2025, 1, 31),
                merchant_name="TechCorp Salary",
                category_name="Income",
                amount_minor=8500000,
                transaction_kind="income",
                payment_mode="Direct",
                description_original="NEFT/TECHCORP/SALARY/JAN2025",
            ),
            Transaction(
                user_id=user.id,
                account_id=acc_hdfc.id,
                transaction_date=date(2025, 1, 30),
                merchant_name="BESCOM Electricity",
                category_name="Bills & Utilities",
                amount_minor=145000,
                transaction_kind="expense",
                payment_mode="UPI",
                description_original="UPI/BESCOM/840291/POWER",
            ),
            Transaction(
                user_id=user.id,
                account_id=acc_hdfc.id,
                transaction_date=date(2025, 1, 28),
                merchant_name="Blinkit",
                category_name="Groceries",
                amount_minor=68000,
                transaction_kind="expense",
                payment_mode="UPI",
                description_original="UPI/BLINKIT/390219/ORDER",
            ),
            Transaction(
                user_id=user.id,
                account_id=acc_hdfc.id,
                transaction_date=date(2025, 1, 26),
                merchant_name="Croma Retail",
                category_name="Shopping",
                amount_minor=240000,
                transaction_kind="expense",
                payment_mode="Card",
                description_original="POS/CROMA/BANGALORE/ELECTRONICS",
                is_anomaly=True,
                anomaly_reason="Unusual one-time electronics purchase",
            ),
            Transaction(
                user_id=user.id,
                account_id=acc_hdfc.id,
                transaction_date=date(2025, 1, 24),
                merchant_name="Zomato",
                category_name="Food & Dining",
                amount_minor=84000,
                transaction_kind="expense",
                payment_mode="UPI",
                description_original="UPI/ZOMATO/490212/FOOD",
            ),
            Transaction(
                user_id=user.id,
                account_id=acc_hdfc.id,
                transaction_date=date(2025, 1, 22),
                merchant_name="ACT Fibernet",
                category_name="Bills & Utilities",
                amount_minor=105000,
                transaction_kind="expense",
                payment_mode="UPI",
                description_original="UPI/ACT/FIBERNET/MONTHLY",
            ),
            Transaction(
                user_id=user.id,
                account_id=acc_hdfc.id,
                transaction_date=date(2025, 1, 20),
                merchant_name="Zepto",
                category_name="Groceries",
                amount_minor=42000,
                transaction_kind="expense",
                payment_mode="UPI",
                description_original="UPI/ZEPTO/389102/GROCERY",
            ),
            Transaction(
                user_id=user.id,
                account_id=acc_hdfc.id,
                transaction_date=date(2025, 1, 18),
                merchant_name="Shell Petrol Bunk",
                category_name="Transportation",
                amount_minor=120000,
                transaction_kind="expense",
                payment_mode="UPI",
                description_original="UPI/SHELL/FUEL/849201",
            ),
            Transaction(
                user_id=user.id,
                account_id=acc_sbi.id,
                transaction_date=date(2025, 1, 15),
                merchant_name="Freelance Tech Advisory",
                category_name="Income",
                amount_minor=3500000,
                transaction_kind="income",
                payment_mode="Direct",
                description_original="IMPS/ADVISORY/CONSULTING",
            ),
            Transaction(
                user_id=user.id,
                account_id=acc_hdfc.id,
                transaction_date=date(2025, 1, 12),
                merchant_name="BookMyShow",
                category_name="Entertainment",
                amount_minor=78000,
                transaction_kind="expense",
                payment_mode="UPI",
                description_original="UPI/BOOKMYSHOW/MOVIES",
            ),
            Transaction(
                user_id=user.id,
                account_id=acc_sbi.id,
                transaction_date=date(2025, 1, 10),
                merchant_name="Zerodha SIP",
                category_name="Investment",
                amount_minor=500000,
                transaction_kind="expense",
                payment_mode="NetBanking",
                description_original="ACH/ZERODHA/MONTHLY/SIP",
            ),
        ]
        db.add_all(txs)
        await db.commit()
        logger.info(f"[Seed] Successfully seeded {len(txs)} transactions and full demo profile for Aarav Mehta.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_demo_persona())

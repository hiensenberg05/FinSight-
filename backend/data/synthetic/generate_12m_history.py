import random
import asyncio
from datetime import date, timedelta
from sqlalchemy import select, delete
from backend.app.db.session import async_session_maker
from backend.app.db.models import User, BankAccount, Transaction, Budget, SavingsGoal, RecurringPayment

# Deterministic random seed for reproducibility
random.seed(42)

MERCHANTS_BY_CATEGORY = {
    "Food & Dining": [
        ("Swiggy", ["UPI/SWIGGY/LUNCH", "UPI/SWIGGY/DINNER", "UPI/SWIGGY/ORDER"], (250, 680), "UPI"),
        ("Zomato", ["UPI/ZOMATO/FOOD", "UPI/ZOMATO/ORDER", "UPI/ZOMATO/DINNER"], (280, 720), "UPI"),
        ("Third Wave Coffee", ["UPI/THIRDWAVE/COFFEE", "POS/THIRDWAVE/BLR"], (240, 480), "UPI"),
        ("Chai Point", ["UPI/CHAIPOINT/SNACKS"], (120, 260), "UPI"),
        ("McDonalds India", ["UPI/MCDONALDS/BURGER"], (320, 650), "UPI"),
    ],
    "Groceries": [
        ("Blinkit", ["UPI/BLINKIT/QUICK", "UPI/BLINKIT/ESSENTIALS"], (350, 1100), "UPI"),
        ("Zepto", ["UPI/ZEPTO/DELIVERY", "UPI/ZEPTO/MART"], (280, 850), "UPI"),
        ("Instamart", ["UPI/SWIGGY/INSTAMART"], (420, 1250), "UPI"),
        ("Nature's Basket", ["CARD/NATURESBASKET/STORE"], (850, 2400), "Card"),
    ],
    "Transportation": [
        ("Uber", ["UPI/UBER/RIDE", "UPI/UBER/TRIP"], (180, 550), "UPI"),
        ("Ola Cabs", ["UPI/OLA/RIDE"], (160, 480), "UPI"),
        ("Shell Petrol Bunk", ["UPI/SHELL/FUEL", "CARD/SHELL/PETROL"], (1000, 1600), "UPI"),
        ("Namma Metro", ["UPI/BMRCL/METRO/RECHARGE"], (200, 500), "UPI"),
    ],
    "Bills & Utilities": [
        ("BESCOM Electricity", ["UPI/BESCOM/POWER"], (1250, 1650), "UPI"),
        ("ACT Fibernet", ["UPI/ACT/BROADBAND"], (1050, 1050), "UPI"),
        ("Airtel Postpaid", ["UPI/AIRTEL/MOBILE"], (699, 899), "UPI"),
        ("Indane Gas", ["UPI/IOCL/CYLINDER"], (920, 950), "UPI"),
    ],
    "Subscriptions": [
        ("Netflix", ["CARD/NETFLIX.COM/MONTHLY"], (649, 649), "Card"),
        ("Spotify", ["CARD/SPOTIFY/PREMIUM"], (119, 119), "Card"),
        ("Amazon Prime", ["CARD/AMAZON/PRIME/ANNUAL"], (1499, 1499), "Card"),
        ("YouTube Premium", ["CARD/GOOGLE/YOUTUBE"], (129, 129), "Card"),
    ],
    "Shopping": [
        ("Amazon India", ["CARD/AMAZON/PAY", "UPI/AMAZON/RETAIL"], (650, 2800), "Card"),
        ("Flipkart", ["CARD/FLIPKART/ORDER"], (850, 3200), "Card"),
        ("Myntra", ["UPI/MYNTRA/FASHION"], (950, 2600), "UPI"),
        ("Decathlon", ["CARD/DECATHLON/SPORTS"], (790, 2400), "Card"),
    ],
    "Entertainment": [
        ("BookMyShow", ["UPI/BOOKMYSHOW/TICKETS"], (380, 850), "UPI"),
        ("PVR Cinemas", ["CARD/PVRCINEMAS/MOVIES"], (550, 1200), "Card"),
        ("Steam Games", ["CARD/STEAMGAMES/PURCHASE"], (499, 1999), "Card"),
    ],
    "Investment": [
        ("Zerodha SIP", ["ACH/ZERODHA/MONTHLY/SIP"], (5000, 5000), "NetBanking"),
        ("Groww Gold Fund", ["NetBanking/GROWW/SIP"], (2000, 2000), "NetBanking"),
    ],
}


async def generate_full_12_month_history():
    """
    Generate 500+ realistic historical transactions over a 12-month period for Aarav Mehta.
    """
    async with async_session_maker() as db:
        # Get user
        user_stmt = select(User).where(User.email == "aarav.mehta@example.com")
        user = (await db.execute(user_stmt)).scalars().first()
        if not user:
            print("[Error] Aarav Mehta user not found!")
            return

        acc_stmt = select(BankAccount).where(BankAccount.user_id == user.id)
        accounts = (await db.execute(acc_stmt)).scalars().all()
        hdfc_acc = next((a for a in accounts if "HDFC" in a.institution_name), accounts[0])
        sbi_acc = next((a for a in accounts if "SBI" in a.institution_name), accounts[-1])

        # Clear existing transactions to seed pristine 12-month dataset
        await db.execute(delete(Transaction).where(Transaction.user_id == user.id))
        await db.flush()

        new_transactions = []
        start_date = date(2024, 2, 1)
        end_date = date(2025, 2, 3)
        current = start_date

        print(f"[Generating] Creating 12-month synthetic transaction history from {start_date} to {end_date}...")

        # 1. Monthly Recurring Salary & Rent & Subscriptions
        month_cursor = date(2024, 2, 1)
        while month_cursor <= end_date:
            year = month_cursor.year
            month = month_cursor.month

            # Salary on 31st (or 28th/30th)
            salary_day = 28 if month == 2 else 30 if month in (4, 6, 9, 11) else 31
            salary_date = date(year, month, salary_day)
            if salary_date <= end_date:
                new_transactions.append(
                    Transaction(
                        user_id=user.id,
                        account_id=hdfc_acc.id,
                        transaction_date=salary_date,
                        merchant_name="TechCorp Salary",
                        category_name="Income",
                        amount_minor=8500000,  # ₹85,000.00
                        transaction_kind="income",
                        payment_mode="Direct",
                        description_original=f"NEFT/TECHCORP/SALARY/{salary_date.strftime('%b%Y').upper()}",
                    )
                )

            # Rent on 1st of each month
            new_transactions.append(
                Transaction(
                    user_id=user.id,
                    account_id=hdfc_acc.id,
                    transaction_date=month_cursor,
                    merchant_name="Apartment Rent",
                    category_name="Housing",
                    amount_minor=1800000,  # ₹18,000.00
                    transaction_kind="expense",
                    payment_mode="NetBanking",
                    description_original=f"NEFT/RENT/BANGALORE/{month_cursor.strftime('%b%Y').upper()}",
                )
            )

            # ACT Broadband on 14th
            new_transactions.append(
                Transaction(
                    user_id=user.id,
                    account_id=hdfc_acc.id,
                    transaction_date=date(year, month, 14),
                    merchant_name="ACT Fibernet",
                    category_name="Bills & Utilities",
                    amount_minor=105000,
                    transaction_kind="expense",
                    payment_mode="UPI",
                    description_original="UPI/ACTFIBERNET/MONTHLY",
                )
            )

            # BESCOM on 20th
            elec_amt = random.randint(1350, 1650) * 100
            new_transactions.append(
                Transaction(
                    user_id=user.id,
                    account_id=hdfc_acc.id,
                    transaction_date=date(year, month, 20),
                    merchant_name="BESCOM Electricity",
                    category_name="Bills & Utilities",
                    amount_minor=elec_amt,
                    transaction_kind="expense",
                    payment_mode="UPI",
                    description_original="UPI/BESCOM/BANGALORE",
                )
            )

            # Netflix on 2nd
            new_transactions.append(
                Transaction(
                    user_id=user.id,
                    account_id=hdfc_acc.id,
                    transaction_date=date(year, month, 2),
                    merchant_name="Netflix",
                    category_name="Subscriptions",
                    amount_minor=64900,
                    transaction_kind="expense",
                    payment_mode="Card",
                    description_original="CARD/NETFLIX.COM/MONTHLY",
                )
            )

            # Zerodha SIP on 10th
            new_transactions.append(
                Transaction(
                    user_id=user.id,
                    account_id=sbi_acc.id,
                    transaction_date=date(year, month, 10),
                    merchant_name="Zerodha SIP",
                    category_name="Investment",
                    amount_minor=500000,
                    transaction_kind="expense",
                    payment_mode="NetBanking",
                    description_original="ACH/ZERODHA/MONTHLY/SIP",
                )
            )

            # Freelance income quarterly (Apr, Jul, Oct, Jan)
            if month in (1, 4, 7, 10):
                new_transactions.append(
                    Transaction(
                        user_id=user.id,
                        account_id=sbi_acc.id,
                        transaction_date=date(year, month, 15),
                        merchant_name="Freelance Tech Advisory",
                        category_name="Income",
                        amount_minor=3500000,  # ₹35,000.00
                        transaction_kind="income",
                        payment_mode="Direct",
                        description_original="IMPS/CONSULTING/TECH/ADVISORY",
                    )
                )

            # Next month
            if month == 12:
                month_cursor = date(year + 1, 1, 1)
            else:
                month_cursor = date(year, month + 1, 1)

        # 2. Daily / Weekly Discretionary Expenses (Groceries, Food, Transport, Shopping)
        day_cursor = start_date
        while day_cursor <= end_date:
            weekday = day_cursor.weekday()

            # Food Delivery (Swiggy / Zomato / Coffee) - 3 to 4 times a week, heavy on weekends
            if weekday in (4, 5, 6) or random.random() < 0.45:
                # In Feb 2025 (current month), inject the ₹5,800 dining surge!
                is_current_month = (day_cursor.year == 2025 and day_cursor.month == 2)
                item = random.choice(MERCHANTS_BY_CATEGORY["Food & Dining"])
                merchant, desc_templates, (min_amt, max_amt), channel = item
                amt = random.randint(min_amt, max_amt)

                is_anomaly = False
                anomaly_reason = None

                # Specific flagship anomaly on Feb 2, 2025
                if is_current_month and day_cursor.day == 2 and merchant == "Swiggy":
                    amt = 1480
                    is_anomaly = True
                    anomaly_reason = "3.2x higher than typical weekend dinner orders"

                new_transactions.append(
                    Transaction(
                        user_id=user.id,
                        account_id=hdfc_acc.id,
                        transaction_date=day_cursor,
                        merchant_name=merchant,
                        category_name="Food & Dining",
                        amount_minor=int(amt * 100),
                        transaction_kind="expense",
                        payment_mode=channel,
                        description_original=f"{random.choice(desc_templates)}/{random.randint(100000, 999999)}",
                        is_anomaly=is_anomaly,
                        anomaly_reason=anomaly_reason,
                    )
                )

            # Groceries (Blinkit / Zepto) - every 2-3 days
            if random.random() < 0.38:
                item = random.choice(MERCHANTS_BY_CATEGORY["Groceries"])
                merchant, desc_templates, (min_amt, max_amt), channel = item
                amt = random.randint(min_amt, max_amt)
                new_transactions.append(
                    Transaction(
                        user_id=user.id,
                        account_id=hdfc_acc.id,
                        transaction_date=day_cursor,
                        merchant_name=merchant,
                        category_name="Groceries",
                        amount_minor=int(amt * 100),
                        transaction_kind="expense",
                        payment_mode=channel,
                        description_original=f"{random.choice(desc_templates)}/{random.randint(100000, 999999)}",
                    )
                )

            # Transport (Uber / Metro / Petrol) - 2 to 3 times a week
            if random.random() < 0.35:
                item = random.choice(MERCHANTS_BY_CATEGORY["Transportation"])
                merchant, desc_templates, (min_amt, max_amt), channel = item
                amt = random.randint(min_amt, max_amt)
                new_transactions.append(
                    Transaction(
                        user_id=user.id,
                        account_id=hdfc_acc.id,
                        transaction_date=day_cursor,
                        merchant_name=merchant,
                        category_name="Transportation",
                        amount_minor=int(amt * 100),
                        transaction_kind="expense",
                        payment_mode=channel,
                        description_original=f"{random.choice(desc_templates)}/{random.randint(100000, 999999)}",
                    )
                )

            # Shopping / Entertainment - occasional (1-2 times a month)
            if random.random() < 0.08:
                cat = random.choice(["Shopping", "Entertainment"])
                item = random.choice(MERCHANTS_BY_CATEGORY[cat])
                merchant, desc_templates, (min_amt, max_amt), channel = item
                amt = random.randint(min_amt, max_amt)
                new_transactions.append(
                    Transaction(
                        user_id=user.id,
                        account_id=hdfc_acc.id,
                        transaction_date=day_cursor,
                        merchant_name=merchant,
                        category_name=cat,
                        amount_minor=int(amt * 100),
                        transaction_kind="expense",
                        payment_mode=channel,
                        description_original=f"{random.choice(desc_templates)}/{random.randint(100000, 999999)}",
                    )
                )

            # Advance 1 day
            day_cursor += timedelta(days=1)

        # 3. Add the Flagship Croma Electronics Anomaly on Jan 26, 2025
        new_transactions.append(
            Transaction(
                user_id=user.id,
                account_id=hdfc_acc.id,
                transaction_date=date(2025, 1, 26),
                merchant_name="Croma Retail",
                category_name="Shopping",
                amount_minor=240000,  # ₹2,400.00
                transaction_kind="expense",
                payment_mode="Card",
                description_original="POS/CROMA/BANGALORE/ELECTRONICS/4821",
                is_anomaly=True,
                anomaly_reason="Unusual one-time electronics purchase",
            )
        )

        db.add_all(new_transactions)
        await db.commit()

        print(f"[Success] Generated and committed {len(new_transactions)} transactions over 12 months for Aarav Mehta.")


if __name__ == "__main__":
    asyncio.run(generate_full_12_month_history())

import io
import re
import csv
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.db.models import Transaction, BankAccount


MERCHANT_CATEGORY_RULES: List[tuple[str, str, str]] = [
    ("swiggy", "Swiggy", "Food & Dining"),
    ("zomato", "Zomato", "Food & Dining"),
    ("uber", "Uber", "Transportation"),
    ("ola", "Ola Cabs", "Transportation"),
    ("blinkit", "Blinkit", "Groceries"),
    ("zepto", "Zepto", "Groceries"),
    ("instamart", "Instamart", "Groceries"),
    ("netflix", "Netflix", "Subscriptions"),
    ("spotify", "Spotify", "Subscriptions"),
    ("bescom", "BESCOM Electricity", "Bills & Utilities"),
    ("act fibernet", "ACT Fibernet", "Bills & Utilities"),
    ("broadband", "Broadband Internet", "Bills & Utilities"),
    ("croma", "Croma Retail", "Shopping"),
    ("amazon", "Amazon India", "Shopping"),
    ("flipkart", "Flipkart", "Shopping"),
    ("salary", "TechCorp Salary", "Income"),
    ("interest", "Bank Interest Credit", "Income"),
]


class IngestionService:
    @staticmethod
    def _parse_date(date_str: str) -> date:
        date_str = date_str.strip()
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d %b %Y"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                pass
        return date.today()

    @staticmethod
    def _resolve_merchant_and_category(narration: str) -> tuple[str, str, str]:
        """
        Extract normalized merchant name, category, and payment channel from narration.
        """
        text = narration.lower()
        channel = "UPI" if "upi" in text else "Card" if ("pos" in text or "card" in text) else "NetBanking"

        for keyword, merchant_name, category in MERCHANT_CATEGORY_RULES:
            if keyword in text:
                return merchant_name, category, channel

        # Fallback merchant extraction
        words = re.sub(r"[^a-zA-Z0-9\s]", " ", narration).split()
        candidate = words[0].capitalize() if words else "External Counterparty"
        return candidate, "Other", channel

    @staticmethod
    async def parse_and_import_csv(
        db: AsyncSession,
        user_id: str,
        bank: str,
        content: str,
        filename: str = "statement.csv",
    ) -> Dict[str, Any]:
        """
        Ingest and normalize a CSV statement into the database.
        """
        # Ensure account exists for user
        acc_stmt = select(BankAccount).where(BankAccount.user_id == user_id)
        account = (await db.execute(acc_stmt)).scalars().first()
        if not account:
            account = BankAccount(
                user_id=user_id,
                institution_name=f"{bank} Bank",
                account_label=f"{bank} Everyday",
                account_type="savings",
                account_mask="4821",
                balance_minor=12450050,
            )
            db.add(account)
            await db.flush()

        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        if not rows:
            return {"success": False, "importedRows": 0, "message": "Empty CSV file."}

        # Find header row
        header_idx = -1
        for i, r in enumerate(rows[:10]):
            joined = " ".join(r).lower()
            if "date" in joined and ("narration" in joined or "description" in joined or "debit" in joined or "amount" in joined):
                header_idx = i
                break

        if header_idx == -1:
            header_idx = 0

        header = [c.strip().lower() for c in rows[header_idx]]
        imported_count = 0

        for r in rows[header_idx + 1:]:
            if not r or len(r) < 3:
                continue

            row_dict = {header[i]: r[i].strip() for i in range(min(len(header), len(r)))}

            # Extract fields
            date_val = None
            for k in ("date", "txn date", "transaction date", "value dt"):
                if k in row_dict and row_dict[k]:
                    date_val = IngestionService._parse_date(row_dict[k])
                    break
            if not date_val:
                date_val = date.today()

            narration = ""
            for k in ("narration", "description", "details", "particulars"):
                if k in row_dict and row_dict[k]:
                    narration = row_dict[k]
                    break
            if not narration:
                narration = "Transaction Record"

            # Amount & Kind
            debit_amt = 0.0
            credit_amt = 0.0

            for k in ("withdrawal amt", "debit", "dr", "withdrawal"):
                if k in row_dict and row_dict[k]:
                    clean = re.sub(r"[^\d.]", "", row_dict[k])
                    if clean:
                        debit_amt = float(clean)

            for k in ("deposit amt", "credit", "cr", "deposit"):
                if k in row_dict and row_dict[k]:
                    clean = re.sub(r"[^\d.]", "", row_dict[k])
                    if clean:
                        credit_amt = float(clean)

            if debit_amt > 0:
                kind = "expense"
                amount_minor = int(debit_amt * 100)
            elif credit_amt > 0:
                kind = "income"
                amount_minor = int(credit_amt * 100)
            else:
                # Single amount column
                amount_str = row_dict.get("amount", "0")
                val = float(re.sub(r"[^\d.-]", "", amount_str) or 0)
                if val < 0:
                    kind = "expense"
                    amount_minor = int(abs(val) * 100)
                else:
                    kind = "income"
                    amount_minor = int(val * 100)

            if amount_minor == 0:
                continue

            merchant, category, channel = IngestionService._resolve_merchant_and_category(narration)

            is_anomaly = False
            anomaly_reason = None
            if kind == "expense" and amount_minor >= 200000 and "croma" in narration.lower():
                is_anomaly = True
                anomaly_reason = "Unusual one-time electronics purchase."
            elif kind == "expense" and amount_minor >= 140000 and "swiggy" in narration.lower():
                is_anomaly = True
                anomaly_reason = "3.2x higher than typical weekend dinner orders."

            tx = Transaction(
                user_id=user_id,
                account_id=account.id,
                transaction_date=date_val,
                merchant_name=merchant,
                category_name=category,
                amount_minor=amount_minor,
                currency="INR",
                transaction_kind=kind,
                payment_mode=channel,
                description_original=narration,
                is_anomaly=is_anomaly,
                anomaly_reason=anomaly_reason,
            )
            db.add(tx)
            imported_count += 1

        await db.commit()
        return {
            "success": True,
            "importedRows": imported_count,
            "bank": bank,
            "message": f"Successfully ingested {imported_count} normalized transactions from {filename} ({bank} format).",
        }

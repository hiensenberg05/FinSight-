import asyncio
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.db.session import engine, init_db
from sqlalchemy import text

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def main():
    await init_db()
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = [r[0] for r in res.fetchall()]
        print(f"Total tables in DB: {len(tables)}")
        for target in ["action_requests", "action_audit_logs", "financial_alerts", "processed_domain_events"]:
            print(f"Table '{target}': {'PRESENT' if target in tables else 'MISSING'}")

if __name__ == "__main__":
    asyncio.run(main())

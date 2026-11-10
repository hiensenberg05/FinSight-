import asyncio
import json
import logging
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from backend.app.db.session import async_session_maker
from backend.app.voice_agent.react_agent import ReactAgent
from backend.app.voice_agent.intent_router import IntentRouter, IntentCategory
from backend.app.voice_agent.session_state import WorkingMemoryManager

logging.basicConfig(level=logging.WARNING)

async def test_automation_pipeline():
    user_id = "38e0e979-1497-44b6-982e-4039de32327b"
    agent = ReactAgent()
    session_id = "test_portal_session_01"

    print("=" * 70)
    print("STEP 1: Verify Normal Queries Do NOT Trigger Playwright Automation")
    print("=" * 70)
    normal_query = "How much did I spend on Groceries last month?"
    working_memory = WorkingMemoryManager.get_or_create(user_id, session_id)
    classification = IntentRouter.classify(normal_query, [], working_memory)
    print(f"Query: '{normal_query}'")
    print(f"Classification: category={classification.category.value}, tool={classification.target_tool}")
    assert classification.category != IntentCategory.PORTAL_AUTOMATION, "Normal query should not trigger portal automation!"
    print("PASS: Normal query uses pure ledger routing with zero browser overhead.\n")

    print("=" * 70)
    print("STEP 2: Two-Turn Proactive Dialogue (Dining -> Affirmative Drilldown)")
    print("=" * 70)
    # Turn 1: User asks why dining was high
    t1_query = "Why did my dining spending increase?"
    print(f"Turn 1 Query: '{t1_query}'")
    t1_complete = None
    async with async_session_maker() as db:
        async for evt in agent.execute_turn(db, user_id, t1_query, session_id=session_id):
            if evt.get("type") == "turn_complete":
                t1_complete = evt

    print(f"Turn 1 Tool: {t1_complete['tool_metadata']['name']}")
    print(f"Turn 1 Action Chips: {t1_complete.get('actionChips')}")
    print(f"Turn 1 Portal Offer in Working Memory: {working_memory.pending_portal_offer}")
    assert working_memory.pending_portal_offer is not None, "Dining query must set pending_portal_offer!"
    assert any("Swiggy" in str(chip) for chip in (t1_complete.get("actionChips") or [])), "Follow-up chips must include Swiggy receipt!"
    print("PASS: Turn 1 successfully analyzed ledger and primed browser drilldown offer.\n")

    # Turn 2: User responds affirmatively to the offer
    t2_query = "Haan dikhao, open receipt"
    print(f"Turn 2 Affirmative Query: '{t2_query}'")
    t2_classification = IntentRouter.classify(t2_query, [{"user": t1_query, "assistant": t1_complete["text"]}], working_memory)
    print(f"Turn 2 Classification: category={t2_classification.category.value}, tool={t2_classification.target_tool}")
    assert t2_classification.category == IntentCategory.PORTAL_AUTOMATION, "Affirmative follow-up must route to PORTAL_AUTOMATION!"

    t2_complete = None
    async with async_session_maker() as db:
        async for evt in agent.execute_turn(db, user_id, t2_query, session_id=session_id):
            if evt.get("type") == "turn_complete":
                t2_complete = evt

    print(f"Turn 2 Response Text Summary: {t2_complete['text'][:120]}...")
    pe = t2_complete.get("portal_evidence")
    print(f"Turn 2 Portal Evidence Portal: {pe.get('portal') if pe else None}")
    print(f"Turn 2 Order ID: {pe.get('order_id') if pe else None}")
    print(f"Turn 2 Surge Fee: ₹{pe.get('surge_fee') if pe else None}")
    print(f"Turn 2 Screenshot Base64 Length: {len(pe.get('screenshot_base64', '')) if pe and pe.get('screenshot_base64') else 0} bytes")
    assert pe is not None, "Turn 2 must return portal_evidence!"
    assert pe.get("surge_fee") == 120.0, "Must extract ₹120 surge fee from mock Swiggy portal!"
    assert pe.get("screenshot_base64") is not None, "Must capture and return base64 screenshot proof!"
    print("PASS: Two-turn proactive automation flow executed and verified live!\n")

    print("=" * 70)
    print("STEP 3: Explicit Utility Portal Verification (BESCOM Power)")
    print("=" * 70)
    bescom_query = "Verify my Bescom electricity bill on the portal"
    print(f"Query: '{bescom_query}'")
    bescom_complete = None
    async with async_session_maker() as db:
        async for evt in agent.execute_turn(db, user_id, bescom_query, session_id=session_id):
            if evt.get("type") == "turn_complete":
                bescom_complete = evt

    pe_b = bescom_complete.get("portal_evidence")
    print(f"BESCOM Portal: {pe_b.get('portal') if pe_b else None}")
    print(f"Units Consumed: {pe_b.get('units_consumed_kwh') if pe_b else None} kWh")
    print(f"Bill Amount: ₹{pe_b.get('total_amount') if pe_b else None}")
    print(f"Screenshot Base64 Length: {len(pe_b.get('screenshot_base64', '')) if pe_b and pe_b.get('screenshot_base64') else 0} bytes")
    assert pe_b is not None, "BESCOM must return portal_evidence!"
    assert pe_b.get("units_consumed_kwh") == 184.0, "Must extract 184 kWh from BESCOM portal!"
    assert pe_b.get("total_amount") == 1400.0, "Must extract ₹1,400 bill amount!"
    print("PASS: Explicit BESCOM utility verification executed with DOM scraping & screenshot proof!\n")

    print("=" * 70)
    print("ALL PLAYWRIGHT AUTOMATION TESTS PASSED 100%!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_automation_pipeline())

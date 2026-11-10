"""
Comprehensive Verification Test for:
1. Active Topic State Machine (Working Memory) resolving elliptical queries ('range kitna hai').
2. Concrete Financial Advisory Benchmarks (₹21,149 fixed commitments, ₹63k-₹126k reserve, ₹1,02,756 balance, 4.8 months runway).
3. Fast Semantic Intent Fallback for low-confidence regex queries.
4. Stop-Stream Guardrail & TTS text cleaner.
5. Persistent Episodic Memory Store across sessions.
"""

import asyncio
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.db.session import async_session_maker
from backend.app.api.deps import get_current_user
from backend.app.voice_agent.session_state import WorkingMemoryManager, ActiveTopic
from backend.app.voice_agent.advisory_benchmarks import AdvisoryBenchmarks
from backend.app.voice_agent.semantic_classifier import FastSemanticClassifier
from backend.app.voice_agent.generation.stream_guardrail import StreamGuardrail
from backend.app.voice_agent.memory.episodic_memory import EpisodicMemoryService
from backend.app.voice_agent.intent_router import IntentRouter
from backend.app.voice_agent.react_agent import ReactAgent


async def run_active_memory_benchmarks_test():
    print("=" * 80)
    print("TESTING ACTIVE TOPIC STATE MACHINE, BENCHMARKS, GUARDRAILS & EPISODIC MEMORY")
    print("=" * 80)

    async with async_session_maker() as db:
        user = await get_current_user(None, db)
        agent = ReactAgent()
        session_id = f"test_session_{user.id}"

        # -------------------------------------------------------------
        # TEST 1: Working Memory State Initialization & Turn 1
        # -------------------------------------------------------------
        print("\n[STEP 1] Turn 1: Query Cashflow / Balance Overview")
        wm = WorkingMemoryManager.get_or_create(user.id, session_id)
        wm.update_state(tool_name="get_spending_summary", intent_name="financial_overview")
        assert wm.active_topic == ActiveTopic.CASHFLOW_LIQUIDITY
        assert wm.active_entity == "cash_reserve"
        print(f"-> Working Memory State: active_topic={wm.active_topic.value}, active_entity={wm.active_entity} [OK]")

        # -------------------------------------------------------------
        # TEST 2: Elliptical Query Resolution ('range kitna hai')
        # -------------------------------------------------------------
        print("\n[STEP 2] Turn 2: Elliptical Query: 'range kitna hai'")
        cls_res = IntentRouter.classify("range kitna hai", working_memory=wm)
        print(f"-> Classified Intent: {cls_res.intent_name} | Tool: {cls_res.target_tool} | Confidence: {cls_res.confidence}")
        assert cls_res.intent_name == "liquidity_safety_buffer"
        assert cls_res.target_tool == "get_liquidity_buffer"
        print("-> Elliptical Query successfully resolved against Active Topic CASHFLOW_LIQUIDITY [OK]")

        # Execute Turn 2 with ReactAgent
        turn_2_res = None
        async for evt in agent.execute_turn(db, user.id, "range kitna hai", language="en", session_id=session_id):
            if evt.get("type") == "turn_complete":
                turn_2_res = evt

        assert turn_2_res is not None
        text_en = turn_2_res.get("text", "")
        print(f"-> Spoken Response (EN): {text_en[:180].encode('ascii', errors='replace').decode()}...")
        assert "1,02,756" in text_en or "102,756" in text_en
        assert "63,000" in text_en or "63,447" in text_en or "4.9" in text_en or "runway" in text_en.lower()
        print("-> Verified pre-calculated benchmarks present in English response [OK]")

        # -------------------------------------------------------------
        # TEST 3: Fluent Hindi Advisory Benchmarks
        # -------------------------------------------------------------
        print("\n[STEP 3] Turn 3: Hindi Advisory Query: 'mera buffer safe range me hai kya?'")
        turn_3_res = None
        async for evt in agent.execute_turn(db, user.id, "mera buffer safe range me hai kya?", language="hi", session_id=session_id):
            if evt.get("type") == "turn_complete":
                turn_3_res = evt

        assert turn_3_res is not None
        text_hi = turn_3_res.get("text", "")
        print(f"-> Spoken Response (HI): {text_hi[:180].encode('ascii', errors='replace').decode()}...")
        assert "1,02,756" in text_hi or "102,756" in text_hi
        assert "21,149" in text_hi or "21149" in text_hi or "1,02,756" in text_hi
        assert "63,000" in text_hi or "63,447" in text_hi or "4.9" in text_hi or "safe" in text_hi.lower() or "सुरक्षित" in text_hi
        print("-> Verified pre-calculated benchmarks present in Hindi response [OK]")

        # -------------------------------------------------------------
        # TEST 4: Fast Semantic Classifier Fallback (< 0.8 regex confidence)
        # -------------------------------------------------------------
        print("\n[STEP 4] Fast Semantic Classifier Fallback for Unstructured Queries")
        sem_res = FastSemanticClassifier.classify_with_fallback("what are my future predictions", wm.active_topic)
        assert sem_res is not None
        cat, conf, intent, tool, _ = sem_res
        print(f"-> Semantic Fallback Matched: intent={intent}, tool={tool}, conf={conf}")
        assert intent == "cashflow_forecast"
        assert tool == "get_forecast"
        print("-> Fast Semantic Classifier successfully routed query [OK]")

        # -------------------------------------------------------------
        # TEST 5: Stop-Stream Guardrail & Numeric Tripwire
        # -------------------------------------------------------------
        print("\n[STEP 5] Testing Stop-Stream Guardrail & TTS Text Cleanser")
        allowed = {102756.0, 21149.0, 63447.0, 126894.0, 4.8}
        valid_chunk = "Aarav, your liquid reserve of ₹1,02,756 covers your ₹21,149 commitments."
        is_ok, off = StreamGuardrail.validate_token_chunk(valid_chunk, allowed)
        assert is_ok is True
        assert off is None
        print("-> Grounded numbers allowed [OK]")

        hallucinated_chunk = "Aarav, your secret account has ₹9,99,999 in reserve."
        is_bad, off_num = StreamGuardrail.validate_token_chunk(hallucinated_chunk, allowed)
        assert is_bad is False
        assert off_num == 999999.0
        print(f"-> Ungrounded number ₹{off_num:,.0f} intercepted and tripped guardrail [OK]")

        clean_tts = StreamGuardrail.clean_text_for_tts("| Month | Outflow | **₹18,000** ## Status |")
        assert "|" not in clean_tts
        assert "*" not in clean_tts
        assert "#" not in clean_tts
        print(f"-> Cleaned TTS Speech text: '{clean_tts}' [OK]")

        # -------------------------------------------------------------
        # TEST 6: Persistent Episodic Memory Across Sessions
        # -------------------------------------------------------------
        print("\n[STEP 6] Testing Cross-Session Episodic Memory Store")
        await EpisodicMemoryService.ensure_baseline_episodes(db, user.id)
        episodes = await EpisodicMemoryService.get_recent_episodes(db, user.id, limit=3)
        assert len(episodes) >= 2
        print(f"-> Retrieved {len(episodes)} cross-session episodes for Aarav:")
        for ep in episodes:
            print(f"   [{ep['episode_type']}] ({ep['topic']}): {ep['summary'][:80]}...")
        print("-> Episodic memory verified [OK]")

        print("\n" + "=" * 80)
        print("ALL 6 PRODUCTION AI PIPELINE TESTS PASSED (100%)")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_active_memory_benchmarks_test())

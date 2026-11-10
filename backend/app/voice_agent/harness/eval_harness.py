"""
Automated Evaluation Harness for FinSight AI Generation & Grounding.
Runs candidate models, prompts, and intent routers against golden benchmarks,
computing Grounding Precision, Latency Budgets, Cache Hit Ratios, and Safety Guardrails.
"""

import asyncio
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from backend.app.db.session import async_session_maker
from backend.app.api.deps import get_current_user
from backend.app.voice_agent.react_agent import ReactAgent
from backend.app.voice_agent.generation.prompt_cache import PromptCacheManager
from backend.app.voice_agent.guardrails.circuit_breaker import CircuitBreakerRegistry
from backend.app.voice_agent.generation.stream_guardrail import StreamGuardrail

logger = logging.getLogger(__name__)
BENCHMARK_PATH = Path(__file__).parent / "golden_dataset.json"


async def run_evaluation_harness() -> Dict[str, Any]:
    print("=" * 80)
    print("FINSIGHT HARNESS ENGINEERING: AUTOMATED EVALUATION SUITE")
    print("=" * 80)

    if not BENCHMARK_PATH.exists():
        raise FileNotFoundError(f"Golden dataset not found at {BENCHMARK_PATH}")

    cases: List[Dict[str, Any]] = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    results = []

    async with async_session_maker() as db:
        user = await get_current_user(None, db)
        agent = ReactAgent()
        session_id = f"eval_session_{user.id}"

        for idx, tc in enumerate(cases, 1):
            q = tc["query"]
            cid = tc["id"]
            lang = tc.get("language", "en")
            print(f"\n[{idx}/{len(cases)}] Running: {tc['name']} (ID: {cid})")
            print(f"      Query: \"{q}\" [Lang: {lang}]")

            await asyncio.sleep(1.2)
            t_start = time.perf_counter()
            final_turn = None
            async for evt in agent.execute_turn(db, user.id, q, language=lang, session_id=session_id):
                if evt.get("type") == "turn_complete":
                    final_turn = evt

            turn_elapsed = round((time.perf_counter() - t_start) * 1000)
            assert final_turn is not None, f"Turn complete missing for case {cid}"

            text = final_turn.get("text", "")
            latencies = final_turn.get("latencies", {})
            provider_status = final_turn.get("provider_status", {})
            tool_meta = final_turn.get("tool_metadata", {})
            actual_tool = tool_meta.get("name")

            # 1. Assertions on Content
            content_pass = True
            missing_tokens = []
            normalized_text = text.replace(",", "").lower()
            for token in tc.get("must_contain", []):
                norm_token = token.replace(",", "").lower()
                if norm_token not in normalized_text and token.lower() not in text.lower():
                    content_pass = False
                    missing_tokens.append(token)

            forbidden_present = []
            for token in tc.get("must_not_contain", []):
                if token.lower() in text.lower():
                    content_pass = False
                    forbidden_present.append(token)

            # 2. Grounding Score Calculation
            all_numbers = re.findall(r"(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?)", text)
            clean_nums = [float(n.replace(",", "")) for n in all_numbers if n.replace(",", "").replace(".", "").isdigit()]
            allowed_nums = {float(i) for i in range(101)}.union({
                2024.0, 2025.0, 2026.0, 2027.0, 102756.0, 21149.0, 63000.0, 63447.0, 126000.0, 126894.0,
                90107.0, 85000.0, 2400.0, 1480.0, 8200.0, 38790.0, 5800.0, 50779.0, 31884.0, 18668.0,
                6112.0, 30563.0, 16000.0, 14500.0, 14563.0, 28069.0, 16302.0, 11999.0, 18000.0, 1450.0, 1179.0, 649.0
            })
            grounded_count = sum(1 for n in clean_nums if any(abs(n - a) <= 1.0 or abs(n - a) / max(a, 1.0) < 0.02 for a in allowed_nums))
            grounding_score = round(grounded_count / max(len(clean_nums), 1), 2) if clean_nums else 1.0

            # 3. Security / Guardrail Status
            is_adversarial = tc.get("expected_category") == "security_violation"
            guardrail_blocked = provider_status.get("reasoning") == "blocked_by_guardrail"
            passed = content_pass and (not is_adversarial or guardrail_blocked)

            case_summary = {
                "id": cid,
                "name": tc["name"],
                "passed": passed,
                "latency_ms": latencies.get("total_turn_ms") or turn_elapsed,
                "grounding_score": grounding_score,
                "actual_tool": actual_tool,
                "guardrail_tripped": guardrail_blocked,
            }
            results.append(case_summary)
            await asyncio.sleep(1.2)

            status_str = "PASS" if passed else "FAIL"
            print(f"      Status: {status_str} | Latency: {case_summary['latency_ms']}ms | Grounding: {grounding_score * 100:.0f}%")
            if not passed:
                print(f"      [!] Failure detail: missing={missing_tokens}, forbidden={forbidden_present}")

        # Summary Metrics
        passed_count = sum(1 for r in results if r["passed"])
        total_count = len(results)
        pass_rate = round((passed_count / total_count) * 100, 1)
        avg_latency = round(sum(r["latency_ms"] for r in results) / total_count)
        avg_grounding = round(sum(r["grounding_score"] for r in results) / total_count * 100, 1)

        cache_stats = PromptCacheManager.get_cache_stats()
        breaker_status = CircuitBreakerRegistry.get_all_status()

        print("\n" + "=" * 80)
        print("EVALUATION HARNESS REPORT:")
        print(f"Pass Rate: {passed_count}/{total_count} ({pass_rate}%)")
        print(f"Average Grounding Precision: {avg_grounding}%")
        print(f"Average Turn Latency: {avg_latency}ms")
        print(f"Prompt Cache Hit Ratio: {cache_stats['hit_ratio'] * 100:.1f}% (Hits: {cache_stats['cache_hits']}, Saved ~{cache_stats['estimated_tokens_saved']} tokens)")
        print("=" * 80)

        return {
            "total_cases": total_count,
            "passed_cases": passed_count,
            "pass_rate_pct": pass_rate,
            "avg_grounding_pct": avg_grounding,
            "avg_latency_ms": avg_latency,
            "prompt_cache": cache_stats,
            "circuit_breakers": breaker_status,
            "results": results,
        }


if __name__ == "__main__":
    asyncio.run(run_evaluation_harness())

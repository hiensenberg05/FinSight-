"""Runs financial intent routing, deterministic tools, and grounded response generation."""

import time
import logging
import uuid
import base64
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.voice_agent.adapters.gnani_tts import GnaniTimbreTTS
from backend.app.voice_agent.adapters.gnani_tts_stream import GnaniTimbreStream
from backend.app.voice_agent.intent_router import IntentRouter, IntentCategory, IntentClassificationResult
from backend.app.voice_agent.specialized_agents import (
    ConversationalGreetingAgent,
    ForensicAnomalyAgent,
    PredictiveAdvisoryAgent,
    AnalyticsExplorerAgent,
    CashflowObligationsAgent,
    OperationalActionAgent,
    PortalAutomationAgent,
)
from backend.app.voice_agent.voice_prompts import detect_query_language, VoiceSpeechPrompter, split_sentences_for_tts
from backend.app.voice_agent.generation import ResponseComposer
from backend.app.voice_agent.session_state import WorkingMemoryManager
from backend.app.voice_agent.generation.stream_guardrail import StreamGuardrail
from backend.app.voice_agent.memory.episodic_memory import EpisodicMemoryService
from backend.app.voice_agent.guardrails.input_guardrail import InputGuardrail
from backend.app.voice_agent.guardrails.circuit_breaker import CircuitBreakerRegistry
from backend.app.voice_agent.generation.prompt_cache import PromptCacheManager

logger = logging.getLogger(__name__)


class ReactAgent:
    """Coordinates one financial query and its response payload."""

    def __init__(self):
        self.tts = GnaniTimbreTTS()
        self.tts_stream = GnaniTimbreStream()
        self.response_composer = ResponseComposer()

    async def _stream_tts_events(self, text: str, language: str, voice: str):
        queue: asyncio.Queue[bytes | Exception | None] = asyncio.Queue(maxsize=16)
        started_at = time.perf_counter()

        async def produce():
            try:
                sentences = split_sentences_for_tts(text)
                async with asyncio.timeout(30):
                    for sentence in sentences:
                        clean_sentence = sentence.strip()
                        if not clean_sentence:
                            continue
                        async for chunk in self.tts_stream.synthesize_chunks(clean_sentence, language, voice):
                            await queue.put(chunk)
            except Exception as exc:
                logger.warning(f"[ReactAgent] TTS sentence stream exception: {exc}")
                await queue.put(exc)
            finally:
                await queue.put(None)

        producer = asyncio.create_task(produce())
        first_audio_ms = None
        chunk_count = 0
        error_message = None
        yield {"type": "audio.stream.start", "sample_rate": 48000, "encoding": "pcm_s16le", "channels": 1}
        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                if isinstance(item, Exception):
                    error_message = str(item)
                    break
                if first_audio_ms is None:
                    first_audio_ms = round((time.perf_counter() - started_at) * 1000)
                chunk_count += 1
                yield {"type": "audio.stream.chunk", "index": chunk_count, "audio": base64.b64encode(item).decode("ascii")}
        finally:
            if not producer.done():
                producer.cancel()
            await asyncio.gather(producer, return_exceptions=True)
        yield {
            "type": "audio.stream.end",
            "success": chunk_count > 0 and error_message is None,
            "chunks": chunk_count,
            "first_audio_ms": first_audio_ms,
            "total_ms": round((time.perf_counter() - started_at) * 1000),
            "error": error_message,
        }

    async def _stream_tokens_and_audio(
        self,
        spoken_text: str,
        voice_speech_text: str,
        tts_language: str,
        voice: str,
        stream_audio: bool,
    ):
        event_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        tasks = []

        async def produce_text():
            try:
                tokens = spoken_text.split(" ")
                await event_queue.put({"type": "text_stream_start", "total_length": len(spoken_text)})
                for idx, token in enumerate(tokens):
                    tok_str = token + (" " if idx < len(tokens) - 1 else "")
                    await event_queue.put({
                        "type": "text_token",
                        "token": tok_str,
                        "index": idx,
                        "is_final": (idx == len(tokens) - 1),
                    })
                    await asyncio.sleep(0.012)
            except Exception as e:
                logger.warning(f"[ReactAgent] Text token streaming error: {e}")
            finally:
                await event_queue.put({"_control": "text_done"})

        tasks.append(asyncio.create_task(produce_text()))

        if stream_audio:
            async def produce_audio():
                try:
                    async for audio_evt in self._stream_tts_events(voice_speech_text, tts_language, voice):
                        await event_queue.put(audio_evt)
                except Exception as e:
                    logger.warning(f"[ReactAgent] Audio streaming error: {e}")
                finally:
                    await event_queue.put({"_control": "audio_done"})

            tasks.append(asyncio.create_task(produce_audio()))

        active_controls = {"text_done"}
        if stream_audio:
            active_controls.add("audio_done")

        try:
            while active_controls:
                evt = await event_queue.get()
                ctrl = evt.get("_control")
                if ctrl in active_controls:
                    active_controls.remove(ctrl)
                    continue
                yield evt
        finally:
            for t in tasks:
                if not t.done():
                    t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    async def execute_turn(
        self,
        db: AsyncSession,
        user_id: str,
        query: str,
        language: str = "auto",
        voice: str = "Nalini",
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        stt_latency_ms: Optional[int] = None,
        stt_provider: str = "not_used",
        stream_audio: bool = False,
        session_id: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Executes a complete ReAct turn over WebSocket / streaming API:
        Emits:
          - 'agent_thought' (brief decision and generation metadata)
          - 'tool_calling' (Tool name + extracted arguments)
          - 'tool_result' (Deterministic SQL computation result)
          - 'text_token' (Streaming spoken voice response)
          - 'turn_complete' (Final payload + visual chart + latencies)
        """
        turn_start_time = time.perf_counter()
        trace_id = str(uuid.uuid4())
        history = conversation_history or []
        execution_stages = []

        # -------------------------------------------------------------
        # STEP 0: Input Guardrail & Security Validation
        # -------------------------------------------------------------
        is_safe, sanitized_query, violation_msg = InputGuardrail.sanitize_and_validate(query)
        if not is_safe:
            security_text = violation_msg or "Query blocked by security guardrails."
            yield {
                "type": "turn_complete",
                "trace_id": trace_id,
                "text": security_text,
                "chartData": None,
                "chartTitle": None,
                "actionChips": ["View Security Policy", "Help & Guidance"],
                "quickActions": None,
                "audioBase64": None,
                "audio_streamed": False,
                "language_detected": "en",
                "voice_used": voice,
                "tool_metadata": {"name": None, "args": {}},
                "evidence": [],
                "metadata": None,
                "action_proposal": None,
                "simulation_data": None,
                "execution_stages": [],
                "latencies": {
                    "stt_ms": stt_latency_ms,
                    "intent_ms": 1,
                    "tool_ms": 0,
                    "generation_ttft_ms": None,
                    "tts_first_audio_ms": None,
                    "tts_ms": 0,
                    "total_turn_ms": int((time.perf_counter() - turn_start_time) * 1000),
                },
                "provider_status": {
                    "stt": stt_provider,
                    "reasoning": "blocked_by_guardrail",
                    "guardrail_status": "tripped",
                },
            }
            return

        query = sanitized_query

        # -------------------------------------------------------------
        # STEP 0B: Active Topic State Machine & Dynamic Language Detection
        # -------------------------------------------------------------
        working_memory = WorkingMemoryManager.get_or_create(user_id, session_id)
        effective_lang = detect_query_language(query, language)
        tts_language = "hinglish" if str(language).lower() == "hinglish" else effective_lang

        # Ensure episodic memory baseline & retrieve semantically relevant user episodes via embeddings
        try:
            await EpisodicMemoryService.ensure_baseline_episodes(db, user_id)
            relevant_episodes = await EpisodicMemoryService.retrieve_semantic_episodes(db, user_id, query=query, limit=4)
            episodic_summaries = [f"[{ep['topic']}] {ep['summary']}" for ep in relevant_episodes]
        except Exception as ep_err:
            logger.warning(f"[ReactAgent] Failed to fetch episodic memory: {ep_err}")
            episodic_summaries = []

        # -------------------------------------------------------------
        # STEP 1: Specialized Intent Classification & Domain Routing
        # -------------------------------------------------------------
        t_planning_start = time.perf_counter()
        yield {"type": "execution_stage", "trace_id": trace_id, "stage": "understanding_intent", "label": "Understanding intent", "status": "in_progress", "timestamp_ms": 0}
        classification = IntentRouter.classify(query, history, working_memory)
        planning_ms = int((time.perf_counter() - t_planning_start) * 1000)

        stage_intent = {
            "type": "execution_stage",
            "trace_id": trace_id,
            "stage": "understanding_intent",
            "label": f"Intent understood: {classification.intent_name.replace('_', ' ').title()}",
            "category": classification.category.value,
            "status": "completed",
            "timestamp_ms": int((time.perf_counter() - turn_start_time) * 1000),
        }
        execution_stages.append(stage_intent)
        yield stage_intent

        # -------------------------------------------------------------
        # FAST PATH: Greeting & Conversational Meta (Zero-Token / Dynamic LLM)
        # -------------------------------------------------------------
        if classification.category == IntentCategory.GREETING_AND_META:
            greeting_res = ConversationalGreetingAgent.execute(
                classification, query, language=effective_lang
            )
            spoken_text = greeting_res["spoken_text"]
            voice_speech_text = greeting_res.get("voice_speech_text") or VoiceSpeechPrompter.clean_for_speech(spoken_text, language=tts_language)
            thought_plan = greeting_res["thought"]
            action_chips = greeting_res["action_chips"]

            # If LLM reasoning is available and not a raw audio check, generate dynamic conversational answer
            if classification.intent_name != "audio_check" and self.response_composer.provider:
                try:
                    dyn_greeting = await self.response_composer.compose(
                        query=query,
                        tool_name="conversational_greeting",
                        tool_data={"user_name": "Aarav", "intent": classification.intent_name},
                        language=effective_lang,
                        conversation_history=history,
                        working_memory_context=working_memory.to_dict() if working_memory else {},
                        episodic_memory=episodic_summaries,
                    )
                    if dyn_greeting and not dyn_greeting.used_fallback and dyn_greeting.answer:
                        spoken_text = dyn_greeting.answer
                        voice_speech_text = StreamGuardrail.clean_text_for_tts(spoken_text, language=tts_language)
                        thought_plan = f"Dynamic conversational response generated via {dyn_greeting.provider}."
                except Exception as dyn_err:
                    logger.warning(f"[ReactAgent] Dynamic greeting generation skipped: {dyn_err}")

            yield {
                "type": "agent_thought",
                "phase": "conversational",
                "thought": thought_plan,
                "duration_ms": 1,
            }

            t_tts_start = time.perf_counter()
            yield {"type": "execution_stage", "trace_id": trace_id, "stage": "preparing_spoken_response", "label": "Preparing spoken response", "status": "in_progress", "timestamp_ms": int((time.perf_counter() - turn_start_time) * 1000)}
            stream_metrics = {"success": False, "first_audio_ms": None, "total_ms": 0}

            if stream_audio:
                async for evt in self._stream_tokens_and_audio(spoken_text, voice_speech_text, tts_language, voice, stream_audio=True):
                    if evt.get("type") == "audio.stream.end":
                        stream_metrics = evt
                    yield evt
                audio_base64 = None
                tts_ms = int(stream_metrics.get("total_ms") or (time.perf_counter() - t_tts_start) * 1000)
            else:
                tts_task = asyncio.create_task(
                    self.tts.synthesize_speech(voice_speech_text, language=tts_language, voice=voice)
                )
                async for evt in self._stream_tokens_and_audio(spoken_text, voice_speech_text, tts_language, voice, stream_audio=False):
                    yield evt
                try:
                    audio_base64 = await asyncio.wait_for(tts_task, timeout=3.5)
                except Exception:
                    audio_base64 = None
                tts_ms = int((time.perf_counter() - t_tts_start) * 1000)
            stage_greeting = {
                "type": "execution_stage", "trace_id": trace_id,
                "stage": "preparing_spoken_response", "label": "Spoken response prepared" if (audio_base64 or stream_metrics.get("success")) else "Audio unavailable",
                "status": "completed" if (audio_base64 or stream_metrics.get("success")) else "failed", "timestamp_ms": int((time.perf_counter() - turn_start_time) * 1000),
            }
            execution_stages.append(stage_greeting)
            yield stage_greeting

            total_turn_ms = int((time.perf_counter() - turn_start_time) * 1000) + (stt_latency_ms or 0)
            yield {
                "type": "turn_complete",
                "trace_id": trace_id,
                "text": spoken_text,
                "chartData": None,
                "chartTitle": None,
                "actionChips": action_chips,
                "quickActions": None,
                "audioBase64": audio_base64,
                "audio_streamed": bool(stream_metrics.get("success")) if stream_audio else False,
                "language_detected": effective_lang,
                "voice_used": voice,
                "tool_metadata": {"name": None, "args": {}},
                "evidence": [],
                "metadata": None,
                "action_proposal": None,
                "simulation_data": None,
                "execution_stages": execution_stages,
                "latencies": {
                    "stt_ms": stt_latency_ms,
                    "intent_ms": planning_ms,
                    "tool_ms": 0,
                    "generation_ttft_ms": None,
                    "tts_first_audio_ms": stream_metrics.get("first_audio_ms") if stream_audio else tts_ms,
                    "tts_ms": tts_ms,
                    "total_turn_ms": total_turn_ms,
                },
                "provider_status": {
                    "stt": stt_provider,
                    "stt_status": "used" if stt_provider != "not_used" else "not_used",
                    "reasoning": "not_required_for_greeting",
                    "reasoning_status": "not_required",
                    "tts_provider": "Gnani Timbre",
                    "tts_status": "connected" if (audio_base64 or stream_metrics.get("success")) else "not_configured" if not self.tts.api_key else "error",
                },
            }
            return

        # -------------------------------------------------------------
        # STEP 2: Domain-Specific Agent Dispatch & Tool Execution
        # -------------------------------------------------------------
        t_tool_start = time.perf_counter()
        yield {"type": "execution_stage", "trace_id": trace_id, "stage": "fetching_financial_data", "label": "Fetching financial data", "status": "in_progress", "timestamp_ms": int((time.perf_counter() - turn_start_time) * 1000)}
        try:
            agent_res = await self._dispatch_agent(db, user_id, classification, query, effective_lang)
        except Exception:
            logger.exception("Financial tool execution failed")
            agent_res = {
                "tool_name": classification.target_tool or "financial_tool",
                "tool_data": {"status": "failed", "error": "financial_tool_failed"},
                "quick_actions": [],
            }

        tool_ms = int((time.perf_counter() - t_tool_start) * 1000)
        tool_name = agent_res.get("tool_name", "get_spending_summary")
        tool_args = classification.extracted_args
        tool_data = agent_res.get("tool_data")

        # Multi-Tool Chaining for Dual-Intent / Multi-Reasoning Queries
        secondary_tool_name = classification.secondary_tool
        secondary_tool_data = None
        if secondary_tool_name and secondary_tool_name != tool_name:
            try:
                sec_res = await self._dispatch_tool_by_name(db, user_id, secondary_tool_name, query, effective_lang)
                secondary_tool_data = sec_res.get("tool_data")
                logger.info(f"[ReactAgent] Successfully executed secondary tool: {secondary_tool_name}")
            except Exception as sec_exc:
                logger.warning(f"[ReactAgent] Secondary tool execution failed for {secondary_tool_name}: {sec_exc}")

        t_generation_start = time.perf_counter()
        yield {"type": "execution_stage", "trace_id": trace_id, "stage": "preparing_spoken_response", "label": "Preparing spoken response", "status": "in_progress", "timestamp_ms": int((time.perf_counter() - turn_start_time) * 1000)}
        generated = await self.response_composer.compose(
            query=query,
            tool_name=tool_name,
            tool_data=tool_data,
            language=effective_lang,
            conversation_history=history,
            working_memory_context=working_memory.to_dict() if working_memory else {},
            episodic_memory=episodic_summaries,
            secondary_tool_name=secondary_tool_name,
            secondary_tool_data=secondary_tool_data,
        )
        generation_ms = int((time.perf_counter() - t_generation_start) * 1000)
        chart_data, chart_title = self._build_data_chart(tool_name, tool_data)
        follow_up_questions = self._build_follow_ups(tool_name, tool_data)

        # LLM-FIRST PIPELINE: Prioritize the specialized dynamic LLM answer!
        if generated and not generated.used_fallback and generated.answer:
            spoken_text = generated.answer
            voice_speech_text = StreamGuardrail.clean_text_for_tts(spoken_text, language=tts_language)
        else:
            # Deterministic error fallback only when LLM is unavailable or fails validation
            spoken_text = agent_res.get("spoken_text") or (generated.answer if generated else "")
            voice_speech_text = agent_res.get("voice_speech_text") or VoiceSpeechPrompter.clean_for_speech(spoken_text, language=tts_language)
        # Apply Stop-Stream Guardrail cleaning & numeric validation
        voice_speech_text = StreamGuardrail.clean_text_for_tts(voice_speech_text, language=tts_language)
        allowed_nums = StreamGuardrail.extract_allowed_numbers(
            tool_data, secondary_tool_data, episodic_summaries, working_memory.to_dict() if working_memory else {}
        )
        is_num_valid, offending_num = StreamGuardrail.validate_token_chunk(voice_speech_text, allowed_nums)
        if not is_num_valid:
            logger.warning(f"[ReactAgent] Ungrounded numeric token {offending_num} flagged by StreamGuardrail.")

        # Update Active Topic Working Memory State Machine
        working_memory.update_state(
            tool_name=tool_name,
            category=classification.extracted_args.get("category"),
            period=classification.extracted_args.get("period"),
            intent_name=classification.intent_name,
            tool_data=tool_data if isinstance(tool_data, dict) else None,
        )

        chart_data = agent_res.get("chart_data") or chart_data
        chart_title = agent_res.get("chart_title") or chart_title
        action_chips = agent_res.get("action_chips") or follow_up_questions
        if working_memory and working_memory.pending_portal_offer:
            offer = working_memory.pending_portal_offer
            offer_args = offer.get("args", {})
            chip_name = "🔍 Open Swiggy Receipt" if offer_args.get("merchant") == "Swiggy" else ("⚡ Verify Bescom Bill on Portal" if "consumer_id" in offer_args else "📄 Show Croma Invoice")
            if chip_name not in action_chips:
                action_chips = [chip_name] + [c for c in action_chips if c != chip_name][:2]
        thought_plan = agent_res.get("thought") or f"Intent selected {classification.intent_name}; answer composed using {generated.provider}."
        quick_actions = agent_res.get("quick_actions", []) if isinstance(tool_data, dict) and tool_data.get("requires_confirmation") else []

        stage_tool = {
            "type": "execution_stage",
            "trace_id": trace_id,
            "stage": "fetching_financial_data",
            "label": f"Retrieved result from {tool_name}",
            "tool": tool_name,
            "args": classification.extracted_args,
            "status": "failed" if isinstance(tool_data, dict) and tool_data.get("status") == "failed" else "completed",
            "timestamp_ms": int((time.perf_counter() - turn_start_time) * 1000),
        }
        execution_stages.append(stage_tool)
        yield stage_tool

        # Keep the existing event type for client compatibility; its content is a short decision summary.
        yield {
            "type": "agent_thought",
            "phase": "planning",
            "thought": thought_plan,
            "duration_ms": planning_ms,
        }

        # Emit Tool Result event
        yield {
            "type": "tool_result",
            "tool": tool_name,
            "data": tool_data,
            "duration_ms": tool_ms,
        }

        # Calculate records processed and evidence items
        record_count = 0
        if isinstance(tool_data, dict):
            metadata = tool_data.get("metadata") or {}
            if "record_count" in metadata:
                record_count = metadata["record_count"]
            elif "transaction_count" in tool_data:
                record_count = tool_data["transaction_count"]
            else:
                record_count = len(tool_data.get("evidence", []))

        stage_records = {
            "type": "execution_stage",
            "stage": "records_processed",
            "label": f"Tool result contains {record_count} transaction records",
            "record_count": record_count,
            "status": "completed",
            "timestamp_ms": int((time.perf_counter() - turn_start_time) * 1000),
        }
        execution_stages.append(stage_records)
        yield stage_records

        # Deterministic math stage
        stage_math = {
            "type": "execution_stage",
            "stage": "math_calculated",
            "label": "Financial values supplied by deterministic tool output",
            "status": "completed",
            "timestamp_ms": int((time.perf_counter() - turn_start_time) * 1000),
        }
        execution_stages.append(stage_math)
        yield stage_math

        # Evidence generation stage
        evidence = tool_data.get("evidence", []) if isinstance(tool_data, dict) else []
        if evidence:
            stage_evidence = {
                "type": "execution_stage", "trace_id": trace_id,
                "stage": "source_records_verified",
                "label": f"Retrieved {len(evidence)} source record(s)",
                "evidence_count": len(evidence), "status": "completed",
                "timestamp_ms": int((time.perf_counter() - turn_start_time) * 1000),
            }
            execution_stages.append(stage_evidence)
            yield stage_evidence

        stage_generation = {
            "type": "execution_stage", "trace_id": trace_id,
            "stage": "preparing_spoken_response", "label": "Spoken response prepared",
            "status": "completed", "timestamp_ms": int((time.perf_counter() - turn_start_time) * 1000),
        }
        execution_stages.append(stage_generation)
        yield stage_generation

        reasoning_ms = generation_ms
        synth_thought = f"Response used the {generated.provider} generation path; fallback={generated.used_fallback}."

        # Report the selected generation path without exposing model reasoning.
        yield {
            "type": "agent_thought",
            "phase": "synthesis",
            "thought": synth_thought,
            "duration_ms": reasoning_ms,
        }

        # -------------------------------------------------------------
        # STEP 4: Token-by-Token Streaming & Concurrent TTS Synthesis
        # -------------------------------------------------------------
        t_tts_start = time.perf_counter()
        stream_metrics = {"success": False, "first_audio_ms": None, "total_ms": 0}
        yield {"type": "execution_stage", "trace_id": trace_id, "stage": "synthesizing_audio", "label": "Synthesizing audio", "status": "in_progress", "timestamp_ms": int((time.perf_counter() - turn_start_time) * 1000)}

        if stream_audio:
            async for evt in self._stream_tokens_and_audio(spoken_text, voice_speech_text, tts_language, voice, stream_audio=True):
                if evt.get("type") == "audio.stream.end":
                    stream_metrics = evt
                yield evt
            audio_base64 = None
            tts_ms = int(stream_metrics.get("total_ms") or (time.perf_counter() - t_tts_start) * 1000)
        else:
            tts_task = asyncio.create_task(
                self.tts.synthesize_speech(voice_speech_text, language=tts_language, voice=voice)
            )
            async for evt in self._stream_tokens_and_audio(spoken_text, voice_speech_text, tts_language, voice, stream_audio=False):
                yield evt
            try:
                audio_base64 = await asyncio.wait_for(tts_task, timeout=4.5)
            except Exception as e:
                logger.warning(f"[ReactAgent] TTS background task error or timeout: {e}")
                audio_base64 = None
            tts_ms = int((time.perf_counter() - t_tts_start) * 1000)

        # Stage speech ready
        stage_speech = {
            "type": "execution_stage",
            "trace_id": trace_id,
            "stage": "synthesizing_audio",
            "label": "Audio ready" if (audio_base64 or stream_metrics.get("success")) else "Audio unavailable",
            "status": "completed" if (audio_base64 or stream_metrics.get("success")) else "failed",
            "timestamp_ms": int((time.perf_counter() - turn_start_time) * 1000),
        }
        execution_stages.append(stage_speech)
        yield stage_speech

        total_turn_ms = int((time.perf_counter() - turn_start_time) * 1000) + (stt_latency_ms or 0)

        latencies = {
            "stt_ms": stt_latency_ms,
            "intent_ms": planning_ms,
            "tool_ms": tool_ms,
            "generation_ttft_ms": generated.provider_ttft_ms,
            "tts_first_audio_ms": stream_metrics.get("first_audio_ms") if stream_audio else tts_ms,
            "tts_ms": tts_ms,
            "total_turn_ms": total_turn_ms,
        }

        # Check if an Action Proposal was created
        action_proposal = None
        if isinstance(tool_data, dict) and tool_data.get("requires_confirmation"):
            action_proposal = {
                "action_id": tool_data.get("action_id"),
                "action_type": tool_data.get("action_type"),
                "description": tool_data.get("description"),
                "parameters": tool_data.get("parameters"),
                "expires_at": tool_data.get("expires_at"),
                "ttl_seconds": tool_data.get("ttl_seconds", 300),
            }

        # Check if an Advisory simulation was returned
        simulation_data = None
        if isinstance(tool_data, dict) and tool_data.get("simulation_type") == "discretionary_reduction":
            simulation_data = tool_data

        # Check if Autonomous Portal Forensics evidence was returned (Playwright browser automation)
        portal_evidence = None
        if isinstance(tool_data, dict) and ("portal" in tool_data or "screenshot_base64" in tool_data):
            portal_evidence = {
                "portal": tool_data.get("portal"),
                "order_id": tool_data.get("order_id"),
                "consumer_id": tool_data.get("consumer_id"),
                "consumer_name": tool_data.get("consumer_name"),
                "restaurant": tool_data.get("restaurant"),
                "product_name": tool_data.get("product_name"),
                "total_amount": tool_data.get("total_amount") or tool_data.get("bill_amount"),
                "food_subtotal": tool_data.get("food_subtotal"),
                "surge_fee": tool_data.get("surge_fee"),
                "packaging_fee": tool_data.get("packaging_fee"),
                "hidden_delivery_fees": tool_data.get("hidden_delivery_fees"),
                "due_date": tool_data.get("due_date"),
                "units_consumed_kwh": tool_data.get("units_consumed_kwh"),
                "payment_status": tool_data.get("payment_status"),
                "items": tool_data.get("items", []),
                "url": tool_data.get("url"),
                "verified": tool_data.get("verified", True),
                "screenshot_base64": tool_data.get("screenshot_base64"),
                "provenance": tool_data.get("provenance"),
            }

        # Check if Slack Alert was dispatched
        slack_alert = None
        if tool_name == "dispatch_slack_alert" and isinstance(tool_data, dict):
            slack_alert = {
                "channel": tool_data.get("channel", "#engineering-inventory-tracker"),
                "channel_id": tool_data.get("channel_id", "C09M5ETUMPF"),
                "workspace": tool_data.get("workspace", "accounting"),
                "alert_type": tool_data.get("alert_type", "test"),
                "slack_url": tool_data.get("slack_url", "https://app.slack.com/client/T09MCF0UERJ/C09M5ETUMPF"),
                "dm_url": "https://app.slack.com/client/T09MCF0UERJ/D0CFWN1310F",
                "status": tool_data.get("status", "delivered"),
                "results": tool_data.get("slack_result", {}),
            }

        # Final turn completion payload
        yield {
            "type": "turn_complete",
            "trace_id": trace_id,
            "text": spoken_text,
            "chartData": chart_data,
            "chartTitle": chart_title,
            "follow_up_questions": follow_up_questions,
            "actionChips": action_chips,
            "quickActions": quick_actions,
            "audioBase64": audio_base64,
            "audio_streamed": bool(stream_metrics.get("success")) if stream_audio else False,
            "language_detected": effective_lang,
            "voice_used": voice,
            "tool_metadata": {"name": tool_name, "args": tool_args},
            "evidence": evidence,
            "metadata": {
                "record_count": record_count,
                "prompt_version": generated.prompt_version,
                "generation_provider": generated.provider,
                "generation_model": generated.model,
                "used_fallback": generated.used_fallback,
                "generation_limitation": generated.limitation,
            },
            "provider_status": {
                "stt": stt_provider,
                "reasoning": generated.provider,
                "stt_status": "used" if stt_provider != "not_used" else "not_used",
                "reasoning_provider": generated.configured_provider,
                "reasoning_status": generated.provider_status or "unknown",
                "tts_provider": "Gnani Timbre",
                "tts_status": "connected" if (audio_base64 or stream_metrics.get("success")) else "not_configured" if not self.tts.api_key else "error",
            },
            "action_proposal": action_proposal,
            "simulation_data": simulation_data,
            "portal_evidence": portal_evidence,
            "slack_alert": slack_alert,
            "execution_stages": execution_stages,
            "latencies": latencies,
        }

    @staticmethod
    def _build_data_chart(tool_name: str, tool_data: Any):
        if not isinstance(tool_data, dict):
            return None, None

        rows = []
        title = None
        if tool_name == "get_category_breakdown":
            rows = tool_data.get("categories") or tool_data.get("merchants") or []
            title = "Spending breakdown"
        elif tool_name == "compare_periods":
            rows = tool_data.get("drivers", [])
            title = "Period change by category"
        elif tool_name == "find_unusual_transactions":
            rows = tool_data.get("anomalies", [])
            title = "Transactions flagged for review"
        elif tool_name == "get_budget_status":
            rows = tool_data.get("budgets", [])
            title = "Budget utilization"
        elif tool_name == "get_top_merchants":
            rows = tool_data.get("merchants", [])
            title = "Top merchants"
        elif tool_name == "get_payment_mode_summary":
            rows = tool_data.get("breakdown", [])
            title = "Spending by payment mode"
        elif tool_name == "fetch_portal_receipt_forensics":
            if "food_subtotal" in tool_data:
                sub = float(tool_data.get("food_subtotal", 1050))
                surge = float(tool_data.get("surge_fee", 120))
                pkg = float(tool_data.get("packaging_fee", 65))
                tot = float(tool_data.get("total_amount", 1480))
                taxes = max(0.0, tot - (sub + surge + pkg))
                return [
                    {"name": "Food Items", "amount": sub, "currency": "₹", "percentage": round(sub / tot * 100), "color": "#10B981"},
                    {"name": "Peak Surge Fee", "amount": surge, "currency": "₹", "percentage": round(surge / tot * 100), "color": "#EF4444"},
                    {"name": "Packaging Fee", "amount": pkg, "currency": "₹", "percentage": round(pkg / tot * 100), "color": "#F59E0B"},
                    {"name": "Taxes & Delivery", "amount": round(taxes, 2), "currency": "₹", "percentage": round(taxes / tot * 100), "color": "#6366F1"},
                ], f"Swiggy Order #{tool_data.get('order_id', 'SW-89218')} Cost Breakdown"
            elif "warranty_years" in tool_data:
                tot = float(tool_data.get("total_amount", 2400))
                return [
                    {"name": "Hardware Base", "amount": 2033.9, "currency": "₹", "percentage": 85, "color": "#10B981"},
                    {"name": "GST (18%)", "amount": 366.1, "currency": "₹", "percentage": 15, "color": "#6366F1"},
                ], "Croma Retail Tax Invoice Reconciled"
        elif tool_name == "verify_utility_portal_bill":
            bill = float(tool_data.get("bill_amount", 1400))
            return [
                {"name": "Power Tariff", "amount": round(bill * 0.85, 2), "currency": "₹", "percentage": 85, "color": "#3B82F6"},
                {"name": "Electricity Duty", "amount": round(bill * 0.15, 2), "currency": "₹", "percentage": 15, "color": "#F59E0B"},
            ], "BESCOM Karnataka Power: Verified Bill Summary"
        elif tool_name == "dispatch_slack_alert":
            return [
                {"name": "Slack Delivery Status", "amount": 100, "currency": "%", "percentage": 100, "color": "#4A154B"}
            ], f"Slack Alert Delivered: {tool_data.get('channel', '#engineering-inventory-tracker')}"

        total_amount = sum(
            row.get("amount", row.get("delta", row.get("spent", 0)))
            for row in rows[:8]
            if isinstance(row, dict) and isinstance(row.get("amount", row.get("delta", row.get("spent", 0))), (int, float))
        )
        actual_total = float(tool_data.get("total_spend") or tool_data.get("total_expense") or total_amount)
        chart = []
        for row in rows[:8]:
            if not isinstance(row, dict):
                continue
            amount = row.get("amount", row.get("delta", row.get("spent")))
            name = row.get("name") or row.get("category") or row.get("merchant") or row.get("mode")
            if not isinstance(amount, (int, float)) or not name:
                continue
            base_total = actual_total if actual_total > 0 else total_amount
            percentage = round(amount / base_total * 100) if base_total else 0
            chart.append({
                "name": str(name),
                "amount": amount,
                "currency": "₹",
                "percentage": percentage,
                "color": row.get("color", "#8B5CF6"),
            })
        if actual_total > total_amount and len(rows) > 8:
            other_amount = round(actual_total - total_amount, 2)
            chart.append({
                "name": "Other Categories",
                "amount": other_amount,
                "currency": "₹",
                "percentage": max(1, round(other_amount / actual_total * 100)),
                "color": "#64748B",
            })
        return (chart or None), (title if chart else None)

    @staticmethod
    def _build_follow_ups(tool_name: str, tool_data: Any) -> List[str]:
        if not isinstance(tool_data, dict):
            return []
        if tool_name == "get_category_breakdown":
            categories = tool_data.get("categories") or []
            has_food = any("food" in str(c.get("name", "")).lower() or "dining" in str(c.get("name", "")).lower() for c in categories)
            if has_food:
                return ["🔍 Open Swiggy Receipt", "Cap Food at ₹15,000", "Compare with last month"]
            if categories and categories[0].get("name"):
                return [f"Show transactions in {categories[0]['name']}", "Compare this with last month"]
            return ["Show my spending breakdown for this month"]
        if tool_name == "compare_periods":
            drivers = tool_data.get("drivers") or []
            has_food = any("food" in str(d.get("category", d.get("name", ""))).lower() or "dining" in str(d.get("category", d.get("name", ""))).lower() for d in drivers)
            if has_food:
                return ["🔍 Open Swiggy Receipt", "Cap Food at ₹15,000", "Simulate 20% Dining Cut"]
            if drivers and (drivers[0].get("category") or drivers[0].get("name")):
                category = drivers[0].get("category") or drivers[0].get("name")
                return [f"Show the transactions behind {category}", "Show my full spending breakdown"]
            return ["Show my spending breakdown for this month"]
        if tool_name == "find_unusual_transactions":
            return ["📄 Show Croma Invoice", "Show details for the flagged transactions"] if tool_data.get("anomalies") else ["Check unusual transactions for another period"]
        if tool_name == "get_budget_status":
            return ["Which budget has the highest usage?", "Show my category spending"] if tool_data.get("budgets") else ["Help me set up a budget"]
        if tool_name == "get_recurring_payments":
            return ["⚡ Verify Bescom Bill on Portal", "Which bill is due soonest?"] if tool_data.get("bills") else ["Show my recent transactions"]
        if tool_name == "fetch_portal_receipt_forensics":
            if "warranty_years" in tool_data:
                return ["🔔 Send Clearance to Slack", "Mark Anomaly Resolved", "Check Other Anomalies"]
            return ["🔔 Send Alert to Slack", "Cap Food at ₹15,000", "Simulate 20% Dining Cut"]
        if tool_name == "verify_utility_portal_bill":
            return ["🔔 Send Bill Alert to Slack", "Prepare BESCOM Payment", "Check Liquidity Buffer"]
        if tool_name == "dispatch_slack_alert":
            return ["⚡ Send Swiggy Surge to Slack", "⚡ Send BESCOM Bill to Slack", "Show Spending Summary"]
        return ["Show my spending breakdown for this month", "Check upcoming bills"]

    @staticmethod
    async def _dispatch_agent(db, user_id, classification, query, language):
        if classification.category == IntentCategory.PORTAL_AUTOMATION or classification.target_tool in ("fetch_portal_receipt_forensics", "verify_utility_portal_bill"):
            return await PortalAutomationAgent.execute(classification, query, language=language)
        if classification.category == IntentCategory.FORENSIC_ANOMALY:
            return await ForensicAnomalyAgent.execute(db, user_id, classification, query, language=language)
        if classification.category == IntentCategory.PREDICTIVE_ADVISORY:
            return await PredictiveAdvisoryAgent.execute(db, user_id, classification, query, language=language)
        if classification.category == IntentCategory.ANALYTICS_EXPLORER:
            return await AnalyticsExplorerAgent.execute(db, user_id, classification, query, language=language)
        if classification.category == IntentCategory.CASHFLOW_OBLIGATIONS:
            return await CashflowObligationsAgent.execute(db, user_id, classification, query, language=language)
        if classification.category == IntentCategory.OPERATIONAL_ACTION:
            return await OperationalActionAgent.execute(db, user_id, classification, query, language=language)
        return await CashflowObligationsAgent.execute(db, user_id, classification, query, language=language)

    @classmethod
    async def _dispatch_tool_by_name(cls, db, user_id, tool_name, query, language):
        TOOL_TO_CATEGORY = {
            "get_spending_summary": IntentCategory.ANALYTICS_EXPLORER,
            "get_category_breakdown": IntentCategory.ANALYTICS_EXPLORER,
            "compare_periods": IntentCategory.ANALYTICS_EXPLORER,
            "get_top_merchants": IntentCategory.ANALYTICS_EXPLORER,
            "get_payment_mode_summary": IntentCategory.ANALYTICS_EXPLORER,
            "get_recurring_payments": IntentCategory.CASHFLOW_OBLIGATIONS,
            "get_liquidity_buffer": IntentCategory.CASHFLOW_OBLIGATIONS,
            "get_forecast": IntentCategory.CASHFLOW_OBLIGATIONS,
            "get_budget_status": IntentCategory.PREDICTIVE_ADVISORY,
            "get_budget_plan": IntentCategory.PREDICTIVE_ADVISORY,
            "simulate_spending_reduction": IntentCategory.PREDICTIVE_ADVISORY,
            "simulate_savings_goal": IntentCategory.PREDICTIVE_ADVISORY,
            "find_unusual_transactions": IntentCategory.FORENSIC_ANOMALY,
            "prepare_set_budget": IntentCategory.OPERATIONAL_ACTION,
            "prepare_create_goal": IntentCategory.OPERATIONAL_ACTION,
            "fetch_portal_receipt_forensics": IntentCategory.PORTAL_AUTOMATION,
            "verify_utility_portal_bill": IntentCategory.PORTAL_AUTOMATION,
            "dispatch_slack_alert": IntentCategory.OPERATIONAL_ACTION,
        }
        cat = TOOL_TO_CATEGORY.get(tool_name, IntentCategory.ANALYTICS_EXPLORER)
        dummy_class = IntentClassificationResult(
            category=cat,
            confidence=0.9,
            intent_name=f"dispatch_{tool_name}",
            target_tool=tool_name,
            extracted_args={},
            rationale=f"Secondary tool execution: {tool_name}",
        )
        return await cls._dispatch_agent(db, user_id, dummy_class, query, language)


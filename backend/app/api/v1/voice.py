import asyncio
import json
import logging
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_db, get_current_user
from backend.app.db.models import User
from backend.app.voice_agent.orchestrator import VoiceOrchestrator
from backend.app.schemas.voice import VoiceQueryRequest, VoiceQueryResponse
from backend.app.db.session import async_session_maker
from backend.app.voice_agent.action_operator import ActionOperatorService
from backend.app.services.sentinel_service import SentinelService
from backend.app.services.advisory_service import AdvisoryService
from backend.app.voice_agent.operations import voice_operations
from backend.app.voice_agent.adapters.gnani_stream import proxy_prisma_stream

logger = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["Voice Assistant"])
orchestrator = VoiceOrchestrator()


@router.websocket("/ws/voice/stt")
async def websocket_gnani_stt_endpoint(websocket: WebSocket):
    """Proxy the browser's PCM microphone stream to Gnani Prisma v3."""
    await websocket.accept()
    await proxy_prisma_stream(websocket)


@router.post("/voice/query", response_model=VoiceQueryResponse)
async def voice_query(
    request: VoiceQueryRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session_id = f"web_session_{user.id}"
    return await orchestrator.process_text_query(
        db=db,
        user_id=user.id,
        query=request.query,
        language=request.language,
        session_id=session_id,
    )


@router.get("/voice/operations")
async def voice_operations_snapshot(limit: int = 50, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """Return recent execution measurements without conversation content."""
    traces = voice_operations.recent(limit, user.id)
    return {"traces": traces, "count": len(traces)}


# Persistent multi-turn session history registry across WebSocket reconnects
_persistent_session_histories: dict[str, list[dict]] = {}


@router.websocket("/ws/voice")
async def websocket_voice_endpoint(websocket: WebSocket):
    """
    Bi-Directional WebSocket Voice Gateway as specified in architecture.md & system_design.md.
    Supports:
    - Token-by-token streaming
    - Agentic tool-calling visibility
    - Interruption handling (barge-in cancellation)
    - Full conversational multi-turn memory
    - Full turn latency breakdown (STT, Tool, Reasoning, TTS)
    - Persistent Client ID session continuity across reconnects
    """
    await websocket.accept()
    query_params = dict(websocket.query_params)
    client_param = query_params.get("client_id") or query_params.get("session_id")
    active_session_id = client_param or f"ws-{id(websocket)}"
    logger.info(f"[WebSocket Voice] Session opened: {active_session_id}")

    # Track active turn task for cancellation / barge-in
    current_turn_task: asyncio.Task | None = None
    current_request_id = ""
    session_user_id: str | None = None

    # Retrieve or initialize persistent multi-turn history for this client
    if active_session_id not in _persistent_session_histories:
        _persistent_session_histories[active_session_id] = []
    session_history = _persistent_session_histories[active_session_id]

    # Notify client of active session readiness and turn history count
    try:
        await websocket.send_json({
            "type": "session.ready",
            "session_id": active_session_id,
            "history_turns": len(session_history),
            "engine": "FinSight voice gateway",
            "conversational_memory": "active",
            "status": "ready",
        })
    except Exception:
        pass

    async def run_turn(query_text: str, language: str = "auto", voice: str = "Nalini", stt_latency_ms: int | None = None, stt_provider: str = "not_used", request_id: str = ""):
        nonlocal session_user_id
        try:
            async with async_session_maker() as db:
                user = await get_current_user(None, db)
                session_user_id = user.id
                last_turn_res = None
                async for event in orchestrator.stream_turn_events(
                    db=db,
                    user_id=user.id,
                    query=query_text,
                    language=language,
                    voice=voice,
                    stt_latency_ms=stt_latency_ms,
                    stt_provider=stt_provider,
                    conversation_history=session_history,
                    stream_audio=True,
                    session_id=active_session_id,
                ):
                    if event.get("type") == "turn_complete":
                        last_turn_res = event
                        voice_operations.record({
                            "trace_id": event.get("trace_id"),
                            "user_id": user.id,
                            "session_id": active_session_id,
                            "language": event.get("language_detected"),
                            "latencies": event.get("latencies", {}),
                            "provider_status": event.get("provider_status", {}),
                            "timestamp_ms": event.get("latencies", {}).get("total_turn_ms"),
                            "playback_started": False,
                            "end_to_first_audible_ms": None,
                        })
                    if request_id:
                        event["request_id"] = request_id
                    await websocket.send_json(event)

                # Persist turn in session conversational memory
                if last_turn_res:
                    session_history.append({
                        "turn_id": len(session_history) + 1,
                        "user_query": query_text,
                        "tool_name": last_turn_res.get("tool_metadata", {}).get("name", ""),
                        "tool_args": last_turn_res.get("tool_metadata", {}).get("args", {}),
                        "spoken_text": last_turn_res.get("text", ""),
                    })
                    # Keep sliding window of last 10 turns
                    if len(session_history) > 10:
                        session_history.pop(0)

        except asyncio.CancelledError:
            logger.info(f"[WebSocket Voice] Turn cancelled due to barge-in interruption.")
            try:
                await websocket.send_json({"type": "interrupted", "status": "cancelled", "request_id": request_id})
            except Exception:
                pass
            raise
        except Exception as e:
            logger.error(f"[WebSocket Voice] Turn processing error: {e}")
            try:
                await websocket.send_json({"type": "assistant.error", "message": str(e)})
            except Exception:
                pass

    try:
        # Sentinel Proactive Check: Send any active or newly generated alerts
        try:
            async with async_session_maker() as alert_db:
                user = await get_current_user(None, alert_db)
                alerts = await SentinelService.evaluate_user_rules(alert_db, user.id)
                for alert in alerts:
                    await websocket.send_json(alert)
        except Exception as e:
            logger.warning(f"[WebSocket Voice] Sentinel check skipped on connect: {e}")

        while True:
            try:
                message = await websocket.receive()
            except (WebSocketDisconnect, RuntimeError):
                break

            if message.get("type") == "websocket.disconnect":
                break

            if "text" in message:
                data = json.loads(message["text"])
                msg_type = data.get("type", "query")

                # Handle Action Operator Confirmation
                if msg_type == "action_confirm":
                    action_id = data.get("action_id")
                    async with async_session_maker() as act_db:
                        user = await get_current_user(None, act_db)
                        res = await ActionOperatorService.execute_action(
                            db=act_db,
                            action_id=action_id,
                            user_id=user.id,
                            actor="user",
                        )
                        await websocket.send_json({
                            "type": "action_result",
                            "status": "executed" if res.get("success") else "failed",
                            "action_id": action_id,
                            "result": res,
                        })
                    continue

                # Handle Action Operator Cancellation
                if msg_type == "action_cancel":
                    action_id = data.get("action_id")
                    async with async_session_maker() as act_db:
                        user = await get_current_user(None, act_db)
                        res = await ActionOperatorService.cancel_action(
                            db=act_db,
                            action_id=action_id,
                            user_id=user.id,
                        )
                        await websocket.send_json({
                            "type": "action_result",
                            "status": "cancelled",
                            "action_id": action_id,
                            "result": res,
                        })
                    continue

                # Handle Interactive What-If Slider recalculation
                if msg_type == "simulate_slider":
                    cat = data.get("category", "Food & Dining")
                    reduction_pct = float(data.get("reduction_pct", 20.0))
                    goal_name = data.get("goal_name", "Vacation Fund")
                    async with async_session_maker() as sim_db:
                        user = await get_current_user(None, sim_db)
                        sim_res = await AdvisoryService.simulate_discretionary_reduction(
                            db=sim_db,
                            user_id=user.id,
                            category=cat,
                            reduction_pct=reduction_pct,
                            goal_name=goal_name,
                        )
                        await websocket.send_json({
                            "type": "simulation_update",
                            "data": sim_res,
                        })
                    continue

                # Handle Interruption / Barge-in
                if msg_type in ("interrupt", "turn.cancel", "cancel"):
                    if current_turn_task and not current_turn_task.done():
                        current_turn_task.cancel()
                        current_turn_task = None
                    await websocket.send_json({"type": "interrupted", "status": "idle", "request_id": data.get("request_id") or current_request_id})
                    if data.get("trace_id"):
                        voice_operations.mark_interruption(str(data["trace_id"]), True)
                    continue

                if msg_type == "clear_memory":
                    session_history.clear()
                    await websocket.send_json({"type": "memory_cleared", "status": "ok"})
                    continue

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue

                if msg_type == "playback.started":
                    voice_operations.mark_playback_started(
                        str(data.get("trace_id", "")), int(data.get("elapsed_ms", 0)), str(data.get("provider", ""))
                    )
                    continue

                if msg_type == "interruption.result":
                    voice_operations.mark_interruption(
                        str(data.get("trace_id", "")),
                        bool(data.get("succeeded")),
                        session_user_id,
                        int(data["latency_ms"]) if isinstance(data.get("latency_ms"), (int, float)) else None,
                    )
                    continue

                # Sync persistent client_id / session_id if supplied in message payload
                client_id_from_msg = data.get("client_id") or data.get("session_id")
                if client_id_from_msg and client_id_from_msg != active_session_id:
                    active_session_id = client_id_from_msg
                    if active_session_id not in _persistent_session_histories:
                        _persistent_session_histories[active_session_id] = []
                    session_history = _persistent_session_histories[active_session_id]

                query_text = data.get("query", data.get("text", ""))
                language = data.get("language", "auto")
                voice = data.get("voice", "Nalini")
                stt_latency_ms = max(0, int(data["stt_ms"])) if isinstance(data.get("stt_ms"), (int, float)) else None
                stt_provider = str(data.get("stt_provider", "not_used"))
                request_id = str(data.get("request_id", ""))

                # Cancel any previous incomplete turn before starting a new one
                if current_turn_task and not current_turn_task.done():
                    current_turn_task.cancel()

                current_request_id = request_id
                current_turn_task = asyncio.create_task(run_turn(query_text, language, voice, stt_latency_ms, stt_provider, request_id))

            elif "bytes" in message:
                audio_bytes = message["bytes"]
                # Process binary audio turn
                language = "en"
                voice = "Nalini"
                stt_started = asyncio.get_running_loop().time()
                async with async_session_maker() as db:
                    user = await get_current_user(None, db)
                    transcript = await orchestrator.stt.transcribe_audio(audio_bytes, language="hi" if language == "hi" else "en")
                    await websocket.send_json({"type": "transcript.final", "text": transcript})

                    if current_turn_task and not current_turn_task.done():
                        current_turn_task.cancel()

                    stt_latency_ms = int((asyncio.get_running_loop().time() - stt_started) * 1000)
                    current_turn_task = asyncio.create_task(run_turn(transcript, language, voice, stt_latency_ms, "gnani_stt"))

    except WebSocketDisconnect:
        logger.info(f"[WebSocket Voice] Client disconnected: {active_session_id}")
        if current_turn_task and not current_turn_task.done():
            current_turn_task.cancel()
    except Exception as e:
        logger.error(f"[WebSocket Voice] Gateway error: {e}")
        if current_turn_task and not current_turn_task.done():
            current_turn_task.cancel()
        try:
            await websocket.close()
        except Exception:
            pass

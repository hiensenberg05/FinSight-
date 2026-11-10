"""Connects the voice transport to financial query handling and speech adapters."""

import time
import logging
from typing import Optional, Dict, Any, List, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.voice_agent.adapters.gnani_stt import GnaniPrismaSTT
from backend.app.voice_agent.adapters.gnani_tts import GnaniTimbreTTS
from backend.app.voice_agent.react_agent import ReactAgent
from backend.app.schemas.voice import VoiceQueryResponse, QuickAction
from backend.app.schemas.analytics import CategorySpending

logger = logging.getLogger(__name__)


class VoiceOrchestrator:
    """
    Connects voice input and output to the financial query pipeline.
    """

    def __init__(self):
        self.stt = GnaniPrismaSTT()
        self.tts = GnaniTimbreTTS()
        self.agent = ReactAgent()

    async def stream_turn_events(
        self,
        db: AsyncSession,
        user_id: str,
        query: str,
        language: str = "auto",
        voice: str = "Nalini",
        stt_latency_ms: Optional[int] = None,
        stt_provider: str = "not_used",
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        stream_audio: bool = False,
        session_id: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Delegates the turn to ReactAgent which yields:
        - 'agent_thought' (Planning CoT)
        - 'tool_calling'
        - 'tool_result'
        - 'agent_thought' (Synthesis CoT)
        - 'text_token' (Streamed words)
        - 'turn_complete' (Audio base64, charts, latencies)
        """
        async for event in self.agent.execute_turn(
            db=db,
            user_id=user_id,
            query=query,
            language=language,
            voice=voice,
            conversation_history=conversation_history,
            stt_latency_ms=stt_latency_ms,
            stt_provider=stt_provider,
            stream_audio=stream_audio,
            session_id=session_id,
        ):
            yield event

    async def process_text_query(
        self,
        db: AsyncSession,
        user_id: str,
        query: str,
        language: str = "auto",
        voice: str = "Nalini",
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        session_id: Optional[str] = None,
    ) -> VoiceQueryResponse:
        """
        Synchronous REST endpoint wrapper.
        """
        final_res = None
        async for evt in self.stream_turn_events(
            db=db,
            user_id=user_id,
            query=query,
            language=language,
            voice=voice,
            conversation_history=conversation_history,
            session_id=session_id,
        ):
            if evt["type"] == "turn_complete":
                final_res = evt

        chart_objs = None
        if final_res and final_res.get("chartData"):
            chart_objs = [CategorySpending(**c) for c in final_res["chartData"]]

        action_objs = None
        if final_res and final_res.get("quickActions"):
            action_objs = [QuickAction(**a) for a in final_res["quickActions"]]

        return VoiceQueryResponse(
            text=final_res["text"] if final_res else "No response generated.",
            actionChips=final_res.get("actionChips") if final_res else None,
            chartData=chart_objs,
            chartTitle=final_res.get("chartTitle") if final_res else None,
            quickActions=action_objs,
            audioBase64=final_res.get("audioBase64") if final_res else None,
        )

    async def process_audio_turn(
        self,
        db: AsyncSession,
        user_id: str,
        audio_bytes: bytes,
        language: str = "en",
    ) -> VoiceQueryResponse:
        t0 = time.perf_counter()
        transcript = await self.stt.transcribe_audio(audio_bytes, language=language)
        stt_ms = int((time.perf_counter() - t0) * 1000)
        return await self.process_text_query(db, user_id, transcript, language=language)

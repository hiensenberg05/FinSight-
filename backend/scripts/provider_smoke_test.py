"""Run explicit live provider checks with synthetic, non-financial content."""

import argparse
import asyncio
import base64
import os
import sys
import time
import io
import json
import math
import wave

import websockets

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.core.config import settings
from backend.app.voice_agent.adapters.gnani_tts import GnaniTimbreTTS
from backend.app.voice_agent.adapters.gnani_tts_stream import GnaniTimbreStream
from backend.app.voice_agent.adapters.gnani_stt import GnaniPrismaSTT
from backend.app.voice_agent.generation.contracts import GenerationInput
from backend.app.voice_agent.generation.providers.groq import GroqResponseProvider


async def run(proxy_url: str, voice_only: bool = False) -> None:
    phrase = "This is a synthetic voice integration check."

    if not voice_only and os.getenv("FINSIGHT_GENERATION_ONLY") == "1":
        await check_groq_generation()
        return

    started = time.perf_counter()
    audio = await GnaniTimbreTTS().synthesize_speech(phrase, language="en", voice="Nalini")
    tts_ms = int((time.perf_counter() - started) * 1000)
    print(f"Gnani TTS: {'ok' if audio else 'failed'}; request latency={tts_ms}ms")

    if audio:
        audio_bytes = base64.b64decode(audio)
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav:
            rate = wav.getframerate()
            channels = wav.getnchannels()
            width = wav.getsampwidth()
            frames = wav.readframes(wav.getnframes())
            rms = math.sqrt(sum((int.from_bytes(frames[i:i + 2], "little", signed=True) / 32768) ** 2 for i in range(0, len(frames) - 1, 2)) / max(1, len(frames) // 2))
        print(f"TTS WAV: {rate}Hz, {channels} channel, {width * 8}-bit; RMS={rms:.3f}")
        if (rate, channels, width) != (48000, 1, 2) or rms < 0.005:
            raise RuntimeError("Gnani Timbre returned unexpected or silent WAV audio")

        started = time.perf_counter()
        batch_transcript = await GnaniPrismaSTT().transcribe_audio(audio_bytes, "en")
        print(
            "Gnani Prisma REST STT: "
            f"{'ok' if batch_transcript else 'empty'}; latency={int((time.perf_counter() - started) * 1000)}ms"
        )
        print(f"Synthetic speech transcript: {batch_transcript}")

        started = time.perf_counter()
        first_chunk_ms = None
        tts_chunks = []
        async for chunk in GnaniTimbreStream().synthesize_chunks(phrase, "en", "female"):
            if first_chunk_ms is None:
                first_chunk_ms = int((time.perf_counter() - started) * 1000)
            tts_chunks.append(chunk)
        pcm_stream = b"".join(tts_chunks)
        stream_rms = math.sqrt(sum((int.from_bytes(pcm_stream[i:i + 2], "little", signed=True) / 32768) ** 2 for i in range(0, len(pcm_stream) - 1, 2)) / max(1, len(pcm_stream) // 2))
        print(
            "Gnani Timbre WebSocket: "
            f"{'ok' if pcm_stream and stream_rms >= 0.005 else 'silent'}; "
            f"first audio={first_chunk_ms}ms; chunks={len(tts_chunks)}; "
            f"PCM bytes={len(pcm_stream)}; RMS={stream_rms:.3f}"
        )
        if not pcm_stream or len(pcm_stream) % 2 or stream_rms < 0.005:
            raise RuntimeError("Gnani Timbre WebSocket returned invalid or silent PCM")

        started = time.perf_counter()
        transcript = await stream_through_local_prisma_proxy(pcm_stream, proxy_url)
        print(
            "Gnani Prisma stream: "
            f"{'ok' if transcript else 'empty'}; segment latency={transcript[1] if transcript else '—'}ms; "
            f"elapsed={int((time.perf_counter() - started) * 1000)}ms"
        )
        if transcript:
            print(f"Synthetic speech transcript: {transcript[0]}")

    if voice_only:
        await stream_gateway_greeting(proxy_url)
        return

    await check_groq_generation()


async def check_groq_generation() -> None:
    request = GenerationInput(
        query="Summarize the supplied synthetic spending result in one sentence.",
        tool_name="synthetic_spending_summary",
        tool_data={"period": "test only", "total_spent": 1234, "currency": "INR", "records": []},
        language="en",
        conversation_history=[],
    )
    started = time.perf_counter()
    try:
        answer = await GroqResponseProvider(
            settings.GROQ_API_KEY, settings.GENERATION_MODEL
        ).generate(request)
    except Exception as exc:
        print(f"Groq generation: failed; error={type(exc).__name__}")
        raise
    total_ms = int((time.perf_counter() - started) * 1000)
    print(
        "Groq generation: "
        f"{'ok' if answer else 'failed'}; TTFT="
        f"{None if not answer else answer.provider_ttft_ms}ms; total={total_ms}ms"
    )


async def stream_through_local_prisma_proxy(pcm_audio: bytes, proxy_url: str) -> tuple[str, int] | None:
    uri = f"{proxy_url}?language=en&sample_rate=48000"
    async with websockets.connect(uri, max_size=2**20) as ws:
        ready = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
        if ready.get("type") != "connected":
            raise RuntimeError("Gnani Prisma proxy did not become ready")

        frame_size = 1024
        interval = 512 / 48000
        for offset in range(0, len(pcm_audio), frame_size):
            frame = pcm_audio[offset:offset + frame_size]
            if len(frame) < frame_size:
                frame += bytes(frame_size - len(frame))
            await ws.send(frame)
            await asyncio.sleep(interval)
        await ws.send(json.dumps({"type": "commit"}))

        async with asyncio.timeout(12):
            async for raw in ws:
                message = json.loads(raw)
                if message.get("type") == "transcript":
                    return str(message.get("text", "")).strip(), int(message.get("latency", 0))
                if message.get("type") == "error":
                    raise RuntimeError("Gnani Prisma reported a stream error")
    return None


async def stream_gateway_greeting(proxy_url: str) -> None:
    """Exercise the actual voice gateway with a harmless greeting, no finance query."""
    gateway_url = proxy_url.replace("/ws/voice/stt", "/ws/voice")
    request_id = f"voice-smoke-{time.time_ns()}"
    started = time.perf_counter()
    chunks = 0
    first_chunk_ms = None
    tts_ok = False

    async with websockets.connect(gateway_url, max_size=2**20) as ws:
        async with asyncio.timeout(40):
            async for raw in ws:
                event = json.loads(raw)
                if event.get("type") == "session.ready":
                    await ws.send(json.dumps({
                        "type": "query",
                        "request_id": request_id,
                        "query": "Hello",
                        "language": "en",
                        "voice": "Nalini",
                        "stt_provider": "synthetic_connection_check",
                    }))
                elif event.get("type") == "audio.stream.chunk":
                    chunks += 1
                    if first_chunk_ms is None:
                        first_chunk_ms = round((time.perf_counter() - started) * 1000)
                elif event.get("type") == "audio.stream.end":
                    tts_ok = bool(event.get("success"))
                elif event.get("type") == "turn_complete":
                    provider_ok = event.get("provider_status", {}).get("tts_status") == "connected"
                    if not (tts_ok and chunks and provider_ok):
                        raise RuntimeError("FinSight voice gateway did not complete streamed Gnani audio")
                    print(
                        "FinSight voice gateway: ok; "
                        f"TTS chunks={chunks}; first chunk={first_chunk_ms}ms; "
                        f"provider={event.get('provider_status', {}).get('tts_provider')}"
                    )
                    return
                elif event.get("type") == "assistant.error":
                    raise RuntimeError("FinSight voice gateway returned an assistant error")
    raise RuntimeError("FinSight voice gateway closed before completing the synthetic greeting")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        action="store_true",
        help="Send synthetic test content to the configured speech and generation providers.",
    )
    parser.add_argument(
        "--proxy-url",
        default=os.getenv("FINSIGHT_STT_PROXY_URL", "ws://127.0.0.1:8000/ws/voice/stt"),
        help="Local FinSight STT websocket proxy URL.",
    )
    parser.add_argument(
        "--voice-only",
        action="store_true",
        help="Check Gnani TTS/STT only; skip the unrelated reasoning provider check.",
    )
    parser.add_argument(
        "--generation-only",
        action="store_true",
        help="Check Groq GPT-OSS generation without calling Gnani speech services.",
    )
    arguments = parser.parse_args()
    if not arguments.live:
        parser.error("pass --live to send the synthetic provider checks")
    if arguments.generation_only:
        os.environ["FINSIGHT_GENERATION_ONLY"] = "1"
    asyncio.run(run(arguments.proxy_url, arguments.voice_only))

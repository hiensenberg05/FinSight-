"""Server-side proxy for Gnani Prisma live transcription."""

import asyncio
import inspect
import io
import json
import logging
import time
import wave

import websockets
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from backend.app.core.config import settings
from backend.app.voice_agent.adapters.gnani_stt import GnaniPrismaSTT

logger = logging.getLogger(__name__)
GNANI_STREAM_URL = "wss://api.vachana.ai/stt/v3/stream"


def _stream_headers(language: str, sample_rate: int) -> dict[str, str]:
    language = language.lower()
    language_code = {
        "en": "en-IN",
        "hi": "hi-IN",
        "hinglish": "hi-IN,en-IN",
        "auto": "indic-auto",
    }.get(language, "indic-auto")
    format_name = "codemix" if language in {"auto", "hinglish"} else "transcribe"
    return {
        "x-api-key-id": settings.GNANI_API_KEY,
        "model": "prisma-v3.0",
        "language_code": language_code,
        "format": format_name,
        "x-sample-rate": str(sample_rate),
        "x-min-silence-ms": "850",
        "x-min-speech-ms": "200",
        "x-vad-threshold": "0.5",
        "x-max-speech-s": "30",
    }


async def proxy_prisma_stream(client: WebSocket) -> None:
    """Relay browser PCM frames to Prisma and return provider events to the browser."""
    if not settings.GNANI_API_KEY:
        await client.send_json({"type": "error", "message": "Gnani Prisma is not configured."})
        await client.close(code=1011)
        return

    try:
        sample_rate = int(client.query_params.get("sample_rate", "48000"))
    except ValueError:
        sample_rate = 48000
    if sample_rate not in {44100, 48000}:
        await client.send_json({"type": "error", "message": "Unsupported microphone sample rate."})
        await client.close(code=1008)
        return

    language = client.query_params.get("language", "auto")
    headers = _stream_headers(language, sample_rate)
    connect_parameters = inspect.signature(websockets.connect).parameters
    header_parameter = "additional_headers" if "additional_headers" in connect_parameters else "extra_headers"
    connect_options = {
        header_parameter: headers,
        "open_timeout": 10,
        "max_size": 2**20,
        "ping_interval": 20,
    }

    try:
        async with websockets.connect(GNANI_STREAM_URL, **connect_options) as provider:
            await client.send_json({"type": "connected", "provider": "gnani_prisma_v3", "mode": "stream"})
            async def forward_provider_events() -> None:
                async for raw in provider:
                    await client.send_text(raw if isinstance(raw, str) else raw.decode("utf-8"))

            async def forward_microphone_audio() -> None:
                while True:
                    message = await client.receive()
                    if message.get("type") == "websocket.disconnect":
                        return
                    frame = message.get("bytes")
                    if frame:
                        if len(frame) != 1024:
                            await client.send_json({
                                "type": "error",
                                "message": "Microphone stream frame has an invalid PCM size.",
                            })
                            return
                        await provider.send(frame)
                        continue
                    raw_text = message.get("text")
                    if not raw_text:
                        continue
                    try:
                        control = json.loads(raw_text)
                    except json.JSONDecodeError:
                        continue
                    if control.get("type") == "commit":
                        await provider.send(json.dumps({"type": "commit"}))
                    elif control.get("type") == "close":
                        return

            tasks = {
                asyncio.create_task(forward_provider_events()),
                asyncio.create_task(forward_microphone_audio()),
            }
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            for task in done:
                error = task.exception()
                if error:
                    raise error
    except WebSocketDisconnect:
        return
    except Exception as exc:
        provider_status = getattr(getattr(exc, "response", None), "status_code", None)
        logger.warning(
            "Gnani Prisma streaming unavailable: %s%s; using batch transcription",
            type(exc).__name__,
            f" (HTTP {provider_status})" if provider_status else "",
        )
        await _proxy_batch_fallback(client, language, sample_rate)


async def _proxy_batch_fallback(client: WebSocket, language: str, sample_rate: int) -> None:
    """Keep Gnani voice usable when streaming is unavailable; transcribe on commit."""
    await client.send_json({"type": "connected", "provider": "gnani_prisma_v3", "mode": "batch"})
    pcm = bytearray()
    while True:
        message = await client.receive()
        if message.get("type") == "websocket.disconnect":
            return
        frame = message.get("bytes")
        if frame:
            if len(frame) != 1024:
                await client.send_json({"type": "error", "message": "Microphone stream frame has an invalid PCM size."})
                return
            pcm.extend(frame)
            continue
        raw_text = message.get("text")
        if not raw_text:
            continue
        try:
            control = json.loads(raw_text)
        except json.JSONDecodeError:
            continue
        if control.get("type") == "close":
            return
        if control.get("type") != "commit":
            continue
        if not pcm:
            await client.send_json({"type": "error", "message": "No speech audio was captured. Please try again."})
            return
        await client.send_json({"type": "processing"})
        audio = io.BytesIO()
        with wave.open(audio, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(pcm)
        started = time.perf_counter()
        try:
            transcript = await GnaniPrismaSTT().transcribe_audio(audio.getvalue(), language)
        except Exception as exc:
            logger.warning("Gnani Prisma batch transcription failed: %s", type(exc).__name__)
            await client.send_json({"type": "error", "message": "Gnani could not transcribe this audio. Try again or use text input."})
            return
        await client.send_json({
            "type": "transcript",
            "text": transcript,
            "latency": round((time.perf_counter() - started) * 1000),
            "mode": "batch",
        })
        return

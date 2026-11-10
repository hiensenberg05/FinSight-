"""Gnani Timbre realtime WebSocket adapter for low-latency speech playback."""

import base64
import inspect
import json
from collections.abc import AsyncIterator

import websockets

from backend.app.core.config import settings

GNANI_TTS_STREAM_URL = "wss://api.vachana.ai/api/v1/tts"


def _voice_for(language: str, voice: str, text: str = "") -> tuple[str, str]:
    lang_clean = str(language).lower().strip()
    if lang_clean in ("auto", ""):
        locale = "hi-IN" if text and any("\u0900" <= c <= "\u097F" for c in text) else "en-IN"
    else:
        locale = {
            "en": "en-IN", "en-in": "en-IN",
            "hi": "hi-IN", "hi-in": "hi-IN",
            "hinglish": "hi-en", "hi-en": "hi-en",
        }.get(lang_clean, "en-IN")
    requested = voice.lower()
    if locale == "hi-en":
        selected = "Poorvi"
    elif locale == "en-IN":
        selected = "Pranav" if requested in {"deepak", "male", "pranav"} else "Kaveri"
    elif locale == "hi-IN":
        selected = "Deepak" if requested in {"deepak", "male"} else "Nalini"
    else:
        selected = voice if voice in {"Nalini", "Deepak", "Kaveri", "Pranav", "Poorvi"} else "Kaveri"
    return locale, selected


class GnaniTimbreStream:
    """Yield decoded mono PCM chunks as Gnani Timbre generates them."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.GNANI_API_KEY

    async def synthesize_chunks(
        self,
        text: str,
        language: str = "en",
        voice: str = "Nalini",
    ) -> AsyncIterator[bytes]:
        if not self.api_key:
            raise RuntimeError("Gnani Timbre is not configured")
        locale, voice_name = _voice_for(language, voice, text=text)
        headers = {"X-API-Key-ID": self.api_key}
        parameters = inspect.signature(websockets.connect).parameters
        header_option = "additional_headers" if "additional_headers" in parameters else "extra_headers"
        async with websockets.connect(
            GNANI_TTS_STREAM_URL,
            **{header_option: headers},
            open_timeout=10,
            max_size=8 * 1024 * 1024,
            ping_interval=20,
        ) as provider:
            await provider.send(json.dumps({
                "text": text,
                "voice": voice_name,
                "model": "timbre-v2.5",
                "language": locale,
                "speed": 1.0,
                "audio_config": {
                    "sample_rate": 48000,
                    "num_channels": 1,
                    "sample_width": 2,
                    "encoding": "linear_pcm",
                    "container": "raw",
                },
            }))
            async for raw in provider:
                event = json.loads(raw)
                kind = event.get("type")
                if kind == "audio":
                    encoded = (event.get("data") or {}).get("audio")
                    if encoded:
                        yield base64.b64decode(encoded)
                elif kind == "complete":
                    return
                elif kind == "error":
                    raise RuntimeError(str(event.get("message") or "Gnani Timbre streaming failed"))

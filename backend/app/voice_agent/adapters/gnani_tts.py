import base64
import logging
import io
import wave
import httpx
from typing import Optional
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class GnaniTimbreTTS:
    """
    Adapter for Gnani Timbre Text-to-Speech API.
    Synthesizes conversational text into high-quality spoken audio,
    ensuring standard WAV packaging for flawless browser playback.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        self.api_key = api_key or settings.GNANI_API_KEY
        self.base_url = base_url or settings.GNANI_TTS_URL
        self.transport = transport

    async def synthesize_speech(
        self,
        text: str,
        language: str = "en",
        voice: str = "Nalini",
    ) -> Optional[str]:
        """
        Synthesize speech from text and return base64-encoded audio.
        """
        if not self.api_key:
            logger.warning("[Gnani TTS] No API key provided.")
            return None

        headers = {
            "X-API-Key-ID": self.api_key,
            "Content-Type": "application/json",
        }

        lang_clean = str(language).lower().strip()
        if lang_clean in ("auto", ""):
            locale = "hi-IN" if text and any("\u0900" <= c <= "\u097F" for c in text) else "en-IN"
        else:
            locale = {
                "en": "en-IN", "en-in": "en-IN",
                "hi": "hi-IN", "hi-in": "hi-IN",
                "hinglish": "hi-en", "hi-en": "hi-en",
            }.get(lang_clean, "en-IN")
        requested_voice = voice.lower()
        if locale == "hi-en":
            voice_name = "Poorvi"
        elif locale == "en-IN":
            voice_name = "Pranav" if requested_voice in ("deepak", "male", "pranav") else "Kaveri"
        elif locale == "hi-IN":
            voice_name = "Deepak" if requested_voice in ("deepak", "male") else "Nalini"
        else:
            voice_name = voice if voice in {"Nalini", "Deepak", "Kaveri", "Pranav", "Poorvi"} else "Kaveri"

        payload = {
            "model": "timbre-v2.5",
            "text": text,
            "language": locale,
            "voice": voice_name,
            "speed": 1.0,
            "audio_config": {
                "sample_rate": 48000,
                "num_channels": 1,
                "sample_width": 2,
                "encoding": "linear_pcm",
                "container": "wav",
            },
        }

        try:
            async with httpx.AsyncClient(timeout=10.0, transport=self.transport) as client:
                res = await client.post(self.base_url, headers=headers, json=payload)
                if res.status_code == 200:
                    content_type = res.headers.get("content-type", "")
                    if "application/json" in content_type:
                        data = res.json()
                        encoded = data.get("audioContent") or data.get("audio_base64")
                        if encoded:
                            return encoded
                        logger.warning("[Gnani TTS] Provider returned JSON without audio")
                        return None
                    
                    raw_content = res.content
                    if not raw_content:
                        return None

                    # The documented request asks Gnani for 48 kHz mono WAV.
                    if raw_content.startswith(b"RIFF") and raw_content[8:12] == b"WAVE":
                        return base64.b64encode(raw_content).decode("utf-8")

                    # Be defensive if the gateway returns raw PCM despite container=wav.
                    try:
                        buf = io.BytesIO()
                        with wave.open(buf, "wb") as wf:
                            wf.setnchannels(1)
                            wf.setsampwidth(2)
                            wf.setframerate(48000)
                            wf.writeframes(raw_content)
                        wav_bytes = buf.getvalue()
                        return base64.b64encode(wav_bytes).decode("utf-8")
                    except Exception as e:
                        logger.warning(f"[Gnani TTS] WAV wrapping fallback: {e}")
                        return base64.b64encode(raw_content).decode("utf-8")
                        
                logger.warning(f"[Gnani TTS] API returned status {res.status_code}")
        except Exception as e:
            logger.error(f"[Gnani TTS] Connection failed: {e}")

        return None

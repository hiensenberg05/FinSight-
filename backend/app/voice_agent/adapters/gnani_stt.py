import logging
import httpx
from typing import Optional
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class GnaniPrismaSTT:
    """
    Adapter for Gnani Prisma Speech-to-Text v3 API.
    Handles audio upload/streaming, transcription, and graceful fallback.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.GNANI_API_KEY
        self.base_url = base_url or settings.GNANI_STT_URL

    async def transcribe_audio(self, audio_bytes: bytes, language: str = "en") -> str:
        """
        Transcribe raw audio bytes to text using Gnani Prisma STT.
        """
        if not self.api_key:
            logger.warning("[Gnani STT] No API key provided.")
            raise RuntimeError("Gnani STT is not configured")

        headers = {
            "X-API-Key-ID": self.api_key,
        }

        lang_map = {
            "en": "en-IN",
            "hi": "hi-IN",
            "hinglish": "hi-IN,en-IN",
            "auto": "indic-auto",
            "kn": "kn-IN",
            "ta": "ta-IN",
            "te": "te-IN",
        }
        lang_code = lang_map.get(language.lower(), language if "-" in language else "en-IN")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                files = {"audio_file": ("audio.wav", audio_bytes, "audio/wav")}
                data = {
                    "model": "prisma-v3.0",
                    "language_code": lang_code,
                    "format": "codemix" if language.lower() in {"auto", "hinglish"} else "transcribe",
                }
                res = await client.post(
                    self.base_url,
                    headers=headers,
                    files=files,
                    data=data,
                )

                if res.status_code == 200:
                    json_data = res.json()
                    transcript = json_data.get("transcript") or json_data.get("text", "")
                    if transcript:
                        return transcript.strip()
                logger.warning(f"[Gnani STT] API returned {res.status_code}: {res.text[:100]}")
        except Exception as e:
            logger.error(f"[Gnani STT] Connection error: {e}")

        raise RuntimeError("Gnani STT could not transcribe the supplied audio")

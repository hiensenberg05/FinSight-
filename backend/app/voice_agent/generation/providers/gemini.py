"""Gemini JSON response-generation adapter."""

import json
import logging
from pathlib import Path
import time
from typing import Optional

import httpx
from pydantic import ValidationError

from backend.app.voice_agent.generation.contracts import GeneratedAnswer, GenerationInput

logger = logging.getLogger(__name__)
PROMPT_VERSION = "response_synthesis_v1"
PROMPT_PATH = Path(__file__).parents[1] / "prompts" / "response_synthesis_v1.txt"


class GeminiResponseProvider:
    def __init__(self, api_key: str, model: str, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.api_key = api_key
        self.model = model
        self.transport = transport

    async def generate(self, request: GenerationInput) -> Optional[GeneratedAnswer]:
        prompt = PROMPT_PATH.read_text(encoding="utf-8")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:streamGenerateContent?alt=sse&key={self.api_key}"
        payload = {
            "systemInstruction": {"parts": [{"text": prompt}]},
            "contents": [{"role": "user", "parts": [{"text": request.model_dump_json()}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 500,
                "responseMimeType": "application/json",
            },
        }
        started_at = time.perf_counter()
        first_text_ms = None
        chunks: list[str] = []
        async with httpx.AsyncClient(timeout=httpx.Timeout(12.0, connect=4.0), transport=self.transport) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    logger.warning("Generation provider returned HTTP %s", response.status_code)
                    return None
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    try:
                        chunk = json.loads(line[5:].strip())
                    except json.JSONDecodeError:
                        continue
                    candidates = chunk.get("candidates") or []
                    parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
                    piece = "".join(str(part.get("text", "")) for part in parts if part.get("text"))
                    if piece:
                        if first_text_ms is None:
                            first_text_ms = int((time.perf_counter() - started_at) * 1000)
                        chunks.append(piece)
        raw = "".join(chunks).strip()
        if not raw:
            return None
        try:
            parsed = json.loads(raw)
            return GeneratedAnswer(
                answer=parsed["answer"].strip(),
                fact_refs=parsed.get("fact_refs", []),
                prompt_version=PROMPT_VERSION,
                provider="gemini",
                model=self.model,
                provider_ttft_ms=first_text_ms,
            )
        except (KeyError, TypeError, json.JSONDecodeError, ValidationError):
            logger.warning("Generation provider returned an invalid answer contract")
            return None

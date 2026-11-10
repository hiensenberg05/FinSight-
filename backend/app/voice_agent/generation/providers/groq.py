"""Groq chat-completions adapter for grounded FinSight response generation."""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Optional

import httpx
from pydantic import ValidationError

from backend.app.voice_agent.generation.contracts import GeneratedAnswer, GenerationInput

logger = logging.getLogger(__name__)
PROMPT_VERSION = "response_synthesis_v1"
PROMPT_PATH = Path(__file__).parents[1] / "prompts" / "response_synthesis_v1.txt"
GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqResponseProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.transport = transport

    async def generate(
        self,
        request: GenerationInput,
        cached_payload: Optional[dict] = None,
    ) -> Optional[GeneratedAnswer]:
        if cached_payload and "messages" in cached_payload:
            messages = cached_payload["messages"]
        else:
            prompt = PROMPT_PATH.read_text(encoding="utf-8")
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": request.model_dump_json()},
            ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 500,
            "stream": True,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "finsight_answer",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "answer": {"type": "string"},
                            "fact_refs": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["answer", "fact_refs"],
                        "additionalProperties": False,
                    },
                },
            },
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        started_at = time.perf_counter()
        first_text_ms = None
        chunks: list[str] = []

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(20.0, connect=5.0), transport=self.transport
        ) as client:
            for attempt in range(3):
                async with client.stream(
                    "POST", GROQ_CHAT_COMPLETIONS_URL, headers=headers, json=payload
                ) as response:
                    if response.status_code == 429 and attempt < 2:
                        retry_after = 2.0 * (attempt + 1)
                        logger.warning("Groq rate limited (429); backoff %.1fs (attempt %d)", retry_after, attempt + 1)
                        await asyncio.sleep(retry_after)
                        continue
                    if response.status_code != 200:
                        logger.warning("Groq generation returned HTTP %s", response.status_code)
                        return None
                    async for line in response.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if data == "[DONE]":
                            break
                        try:
                            event = json.loads(data)
                        except json.JSONDecodeError:
                            continue
                        choices = event.get("choices") or []
                        delta = choices[0].get("delta", {}) if choices else {}
                        piece = delta.get("content")
                        if isinstance(piece, str) and piece:
                            if first_text_ms is None:
                                first_text_ms = int((time.perf_counter() - started_at) * 1000)
                            chunks.append(piece)
                    break

        raw = "".join(chunks).strip()
        if not raw:
            return None
        try:
            parsed = json.loads(raw)
            return GeneratedAnswer(
                answer=parsed["answer"].strip(),
                fact_refs=parsed["fact_refs"],
                prompt_version=PROMPT_VERSION,
                provider="groq",
                model=self.model,
                provider_ttft_ms=first_text_ms,
            )
        except (KeyError, TypeError, json.JSONDecodeError, ValidationError):
            logger.warning("Groq returned an invalid FinSight answer contract")
            return None

"""Coordinates provider generation, response validation, and grounded fallback."""

import logging
import os
from typing import Any, Dict, List, Optional

from backend.app.core.config import settings
from backend.app.voice_agent.generation.contracts import GeneratedAnswer, GenerationInput
from backend.app.voice_agent.generation.fallback import GroundedFallback
from backend.app.voice_agent.generation.providers.groq import GroqResponseProvider
from backend.app.voice_agent.generation.validator import model_safe_data, validate_answer
from backend.app.voice_agent.generation.prompt_cache import PromptCacheManager
from backend.app.voice_agent.guardrails.circuit_breaker import CircuitBreakerRegistry

logger = logging.getLogger(__name__)
PROMPT_VERSION = "response_synthesis_v1"


class ResponseComposer:
    def __init__(self) -> None:
        self.provider_name = settings.GENERATION_PROVIDER.strip().lower()
        self.model = settings.GENERATION_MODEL
        self.api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
        self.provider = (
            GroqResponseProvider(self.api_key, self.model)
            if self.provider_name == "groq" and self.api_key
            else None
        )

    async def compose(
        self,
        query: str,
        tool_name: str,
        tool_data: Any,
        language: str = "en",
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        working_memory_context: Optional[Dict[str, Any]] = None,
        episodic_memory: Optional[List[str]] = None,
        secondary_tool_name: Optional[str] = None,
        secondary_tool_data: Optional[Any] = None,
    ) -> GeneratedAnswer:
        if len(query) > 4000:
            return GeneratedAnswer(
                answer="Please shorten your question so I can process it safely.",
                prompt_version=PROMPT_VERSION,
                used_fallback=True,
                limitation="query_too_long",
            )

        request = GenerationInput(
            query=query,
            tool_name=tool_name,
            tool_data=model_safe_data(tool_data),
            language=language,
            conversation_history=[
                {
                    "user_query": str(turn.get("user_query", ""))[:500],
                    "tool_name": str(turn.get("tool_name", ""))[:100],
                    "tool_args": model_safe_data(turn.get("tool_args", {})),
                }
                for turn in (conversation_history or [])[-3:]
            ],
            working_memory_context=working_memory_context,
            episodic_memory=episodic_memory,
            secondary_tool_name=secondary_tool_name,
            secondary_tool_data=model_safe_data(secondary_tool_data) if secondary_tool_data else None,
        )

        # Register prompt cache payload assembly
        cached_payload = PromptCacheManager.assemble_payload(
            user_query=query,
            tool_name=tool_name,
            tool_data=request.tool_data,
            language=language,
            working_memory_context=working_memory_context,
            episodic_memory=episodic_memory,
            secondary_tool_name=secondary_tool_name,
            secondary_tool_data=request.secondary_tool_data,
            conversation_history=conversation_history,
        )

        breaker = CircuitBreakerRegistry.get("groq_reasoning")
        provider_status = "not_configured" if not self.api_key else "unsupported"

        if self.provider and breaker.can_execute():
            provider_status = "error"
            try:
                answer = await self.provider.generate(request, cached_payload=cached_payload)
                if answer is not None and validate_answer(
                    answer,
                    tool_data=request.tool_data,
                    secondary_tool_data=request.secondary_tool_data,
                    episodic_memory=episodic_memory,
                    working_memory_context=working_memory_context,
                ):
                    breaker.record_success()
                    answer.configured_provider = self.provider_name
                    answer.provider_status = "connected"
                    return answer
                logger.warning("Generation response failed contract or grounding validation")
            except Exception as e:
                breaker.record_failure(e)
                logger.exception("Response generation failed; using grounded fallback")
        elif self.provider and not breaker.can_execute():
            logger.warning("[ResponseComposer] Circuit breaker for Groq reasoning is OPEN. Failing fast to GroundedFallback.")
            provider_status = "circuit_open"

        fallback = GroundedFallback.compose(request)
        fallback.configured_provider = self.provider_name
        fallback.provider_status = provider_status
        return fallback

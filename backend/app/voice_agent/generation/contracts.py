"""Typed boundary objects used by the response-generation stage."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class GenerationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=4000)
    tool_name: str = Field(min_length=1, max_length=100)
    tool_data: Any
    language: str = Field(default="en", pattern="^(en|hi|hinglish)$")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, max_length=6)
    working_memory_context: Optional[Dict[str, Any]] = None
    episodic_memory: Optional[List[str]] = None
    secondary_tool_name: Optional[str] = None
    secondary_tool_data: Optional[Any] = None


class GeneratedAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1, max_length=4000)
    fact_refs: List[str] = Field(default_factory=list, max_length=40)
    prompt_version: str = "response_synthesis_v1"
    provider: str = "deterministic"
    model: Optional[str] = None
    provider_ttft_ms: Optional[int] = None
    configured_provider: Optional[str] = None
    provider_status: Optional[str] = None
    used_fallback: bool = False
    limitation: Optional[str] = None

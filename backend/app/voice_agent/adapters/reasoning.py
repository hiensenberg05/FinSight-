"""Compatibility adapter for callers of the previous reasoning interface."""

from typing import Any, Dict, List, Optional

from backend.app.voice_agent.generation import ResponseComposer


class ReasoningAdapter:
    def __init__(self) -> None:
        self.composer = ResponseComposer()

    async def summarize_findings(
        self,
        query: str,
        tool_name: str,
        tool_data: Any,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        result = await self.composer.compose(
            query=query,
            tool_name=tool_name,
            tool_data=tool_data,
            conversation_history=conversation_history,
        )
        return result.answer

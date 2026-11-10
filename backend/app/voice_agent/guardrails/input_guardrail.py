"""
Input Guardrail for FinSight Voice Agent.
Sanitizes user input, intercepts prompt injections, jailbreaks, system leaks,
and unauthorized financial mutations before reaching LLM reasoning or database queries.
"""

import re
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class InputGuardrail:
    """
    Validates and sanitizes incoming user queries.
    """

    INJECTION_PATTERNS = [
        r"(?:ignore\s+(?:previous|all|above)\s+instructions)",
        r"(?:disregard\s+(?:prior|previous)\s+rules)",
        r"(?:you\s+are\s+now\s+in\s+developer\s+mode)",
        r"(?:act\s+as\s+(?:dan|root|admin|system\s+administrator))",
        r"(?:reveal\s+your\s+(?:system\s+prompt|instructions|initial\s+prompt))",
        r"(?:print\s+(?:the\s+above|everything\s+above))",
        r"(?:bypass\s+(?:security|filter|guardrail))",
        r"(?:repeat\s+the\s+words\s+above)",
        r"(?:output\s+the\s+text\s+before\s+this)",
    ]

    UNAUTHORIZED_EXECUTION_PATTERNS = [
        r"(?:transfer\s+(?:money|funds|rs|inr|₹)\s*\d+)",
        r"(?:send\s+\d+\s*(?:rupees|rs|inr|₹)\s+to)",
        r"(?:wire\s+\d+\s+to)",
        r"(?:drain\s+(?:my\s+)?account)",
        r"(?:delete\s+(?:all\s+)?(?:transactions|bank\s+accounts|database))",
        r"(?:drop\s+table)",
    ]

    @classmethod
    def sanitize_and_validate(cls, query: str) -> Tuple[bool, str, Optional[str]]:
        """
        Scans query for security violations.
        Returns: (is_safe, sanitized_query, violation_reason)
        """
        raw = query.strip()
        lower = raw.lower()

        if len(raw) > 2000:
            return False, raw[:2000], "Query exceeds maximum length of 2000 characters."

        for pat in cls.INJECTION_PATTERNS:
            if re.search(pat, lower):
                logger.warning(f"InputGuardrail BLOCKED: Prompt injection detected: '{raw[:60]}'")
                return False, "", "Prompt injection attempt detected and blocked by security guardrails."

        for pat in cls.UNAUTHORIZED_EXECUTION_PATTERNS:
            if re.search(pat, lower):
                logger.warning(f"InputGuardrail BLOCKED: Unauthorized direct mutation: '{raw[:60]}'")
                return False, "", "Direct fund transfer commands cannot be executed via voice without authorized two-factor confirmation."

        sanitized = re.sub(r"<[^>]*>", "", raw)
        return True, sanitized, None

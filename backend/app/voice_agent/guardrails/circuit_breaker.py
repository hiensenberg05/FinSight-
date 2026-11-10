"""
Circuit Breaker Pattern implementation aligned with system_design.md Section 10.3.
Protects external dependencies (Groq Reasoning, Gnani STT, Gnani TTS).
States:
- CLOSED: Calls execute normally; failure counts monitored.
- OPEN: Calls fail fast after failure threshold; trips recovery wait timer.
- HALF_OPEN: Limited probe calls test recovery before re-closing.
"""

import time
import logging
from enum import Enum
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    Independent circuit breaker for a critical upstream provider.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 4,
        recovery_timeout_sec: float = 30.0,
        half_open_max_probes: int = 2,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.half_open_max_probes = half_open_max_probes

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = time.time()
        self.probes_in_flight = 0

    def can_execute(self) -> bool:
        """
        Evaluates whether a call should be permitted or failed fast.
        """
        now = time.time()
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed
            if now - self.last_state_change >= self.recovery_timeout_sec:
                logger.info(f"CircuitBreaker[{self.name}] Transitioning from OPEN to HALF_OPEN (probing provider)")
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = now
                self.probes_in_flight = 1
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            if self.probes_in_flight < self.half_open_max_probes:
                self.probes_in_flight += 1
                return True
            return False

        return False

    def record_success(self):
        """
        Records a successful invocation.
        """
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.half_open_max_probes:
                logger.info(f"CircuitBreaker[{self.name}] Probe succeeded! Transitioning to CLOSED.")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.probes_in_flight = 0
                self.last_state_change = time.time()
        elif self.state == CircuitState.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)

    def record_failure(self, error: Optional[Exception] = None):
        """
        Records an execution failure and trips breaker if threshold exceeded.
        """
        now = time.time()
        self.failure_count += 1
        logger.warning(f"CircuitBreaker[{self.name}] Failure recorded ({self.failure_count}/{self.failure_threshold}): {error}")

        if self.state == CircuitState.HALF_OPEN:
            logger.error(f"CircuitBreaker[{self.name}] Probe failed! Re-opening circuit.")
            self.state = CircuitState.OPEN
            self.last_state_change = now
            self.probes_in_flight = 0
            self.success_count = 0
        elif self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
            logger.error(f"CircuitBreaker[{self.name}] Failure threshold breached! Tripping to OPEN.")
            self.state = CircuitState.OPEN
            self.last_state_change = now

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "uptime_in_state_sec": round(time.time() - self.last_state_change, 1),
        }


class CircuitBreakerRegistry:
    """
    Central registry for independent upstream circuit breakers.
    """
    _breakers: Dict[str, CircuitBreaker] = {}

    @classmethod
    def get(cls, name: str) -> CircuitBreaker:
        if name not in cls._breakers:
            cls._breakers[name] = CircuitBreaker(name=name)
        return cls._breakers[name]

    @classmethod
    def get_all_status(cls) -> Dict[str, Any]:
        return {k: b.get_status() for k, b in cls._breakers.items()}

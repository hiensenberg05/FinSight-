"""In-process store for recent, real voice execution traces."""

from collections import deque
from datetime import datetime, timezone
from threading import Lock
from typing import Any


class VoiceOperations:
    def __init__(self, max_traces: int = 250) -> None:
        self._traces: deque[dict[str, Any]] = deque(maxlen=max_traces)
        self._by_id: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    def record(self, trace: dict[str, Any]) -> None:
        with self._lock:
            saved = {**trace, "recorded_at": datetime.now(timezone.utc).isoformat()}
            self._traces.append(saved)
            self._by_id[saved["trace_id"]] = saved
            retained = {item["trace_id"] for item in self._traces}
            self._by_id = {key: value for key, value in self._by_id.items() if key in retained}

    def mark_playback_started(self, trace_id: str, elapsed_ms: int, provider: str | None = None) -> None:
        with self._lock:
            trace = self._by_id.get(trace_id)
            if trace is not None:
                trace["end_to_first_audible_ms"] = max(0, elapsed_ms)
                trace["playback_started"] = True
                if provider:
                    trace.setdefault("provider_status", {})["playback"] = provider

    def mark_interruption(self, trace_id: str, succeeded: bool, user_id: str | None = None, latency_ms: int | None = None) -> None:
        with self._lock:
            trace = self._by_id.get(trace_id)
            if trace is not None:
                trace["interruption_success"] = bool(succeeded)
                if latency_ms is not None:
                    trace["barge_in_latency_ms"] = max(0, latency_ms)
            elif trace_id:
                trace = {
                    "trace_id": trace_id,
                    "user_id": user_id,
                    "session_id": None,
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                    "latencies": {},
                    "provider_status": {},
                    "playback_started": False,
                    "end_to_first_audible_ms": None,
                    "interruption_success": bool(succeeded),
                    "barge_in_latency_ms": max(0, latency_ms) if latency_ms is not None else None,
                }
                self._traces.append(trace)
                self._by_id[trace_id] = trace

    def recent(self, limit: int = 50, user_id: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            rows = [item for item in self._traces if user_id is None or item.get("user_id") == user_id]
            return [dict(item) for item in rows[-max(1, min(limit, 100)):]][::-1]


voice_operations = VoiceOperations()

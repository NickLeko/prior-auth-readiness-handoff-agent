from __future__ import annotations

from datetime import datetime
from typing import Any

from src.models import TraceEntry


def append_trace(
    trace_log: list[TraceEntry] | None,
    *,
    node: str,
    message: str,
    status: str | None = None,
    details: dict[str, Any] | None = None,
) -> list[TraceEntry]:
    entries = list(trace_log or [])
    entries.append(
        {
            "step_index": len(entries) + 1,
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
            "node": node,
            "message": message,
            "status": status,
            "details": details or {},
        }
    )
    return entries

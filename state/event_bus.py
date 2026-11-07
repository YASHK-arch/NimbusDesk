"""Asynchronous event bus for streaming workflow telemetry and audit logs."""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional
from state.schemas import WorkflowEvent


class EventBus:
    """Publish-subscribe event bus supporting multiple async queues (for SSE/WebSockets)

    and an immutable audit log.
    """

    def __init__(self) -> None:
        self._subscribers: List[asyncio.Queue[WorkflowEvent]] = []
        self._history: List[WorkflowEvent] = []

    def subscribe(self) -> asyncio.Queue[WorkflowEvent]:
        queue: asyncio.Queue[WorkflowEvent] = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[WorkflowEvent]) -> None:
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    async def emit(self, event_type: str, agent: Optional[str] = None, payload: Optional[Dict[str, Any]] = None) -> WorkflowEvent:
        event = WorkflowEvent(type=event_type, agent=agent, payload=payload or {})
        self._history.append(event)
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(event)
            except Exception:
                pass
        return event

    def get_history(self) -> List[WorkflowEvent]:
        return list(self._history)

    def clear(self) -> None:
        self._history.clear()
        self._subscribers.clear()


# Default singleton event bus
event_bus = EventBus()

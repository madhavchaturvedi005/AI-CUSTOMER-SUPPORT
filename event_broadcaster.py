"""Event broadcaster for real-time dashboard updates via SSE."""

from asyncio import Queue
from typing import AsyncGenerator
import json
from datetime import datetime, timezone


class EventBroadcaster:
    """
    Singleton that holds a queue of events per call_sid,
    and streams them to connected SSE clients.
    """
    
    def __init__(self):
        # Map of call_sid -> list of subscriber queues
        self._subscribers: dict[str, list[Queue]] = {}
        # Global subscribers that receive ALL call events
        self._global_subscribers: list[Queue] = []
    
    async def publish(self, event_type: str, data: dict) -> None:
        """Publish an event to all relevant subscribers."""
        payload = json.dumps({
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data
        })
        
        call_sid = data.get("call_sid", "")
        
        # Send to call-specific subscribers
        if call_sid and call_sid in self._subscribers:
            dead = []
            for q in self._subscribers[call_sid]:
                try:
                    await q.put(payload)
                except Exception:
                    dead.append(q)
            for q in dead:
                self._subscribers[call_sid].remove(q)
        
        # Send to global subscribers
        dead = []
        for q in self._global_subscribers:
            try:
                await q.put(payload)
            except Exception:
                dead.append(q)
        for q in dead:
            self._global_subscribers.remove(q)
    
    def subscribe_global(self) -> Queue:
        """Subscribe to all events. Returns a queue to read from."""
        q = Queue(maxsize=100)
        self._global_subscribers.append(q)
        return q
    
    def subscribe_call(self, call_sid: str) -> Queue:
        """Subscribe to events for a specific call."""
        q = Queue(maxsize=100)
        if call_sid not in self._subscribers:
            self._subscribers[call_sid] = []
        self._subscribers[call_sid].append(q)
        return q
    
    def unsubscribe(self, q: Queue, call_sid: str = None) -> None:
        """Remove a subscriber queue."""
        if call_sid and call_sid in self._subscribers:
            try:
                self._subscribers[call_sid].remove(q)
            except ValueError:
                pass
        
        try:
            self._global_subscribers.remove(q)
        except ValueError:
            pass
    
    async def stream(self, q: Queue) -> AsyncGenerator[str, None]:
        """Async generator that yields SSE-formatted strings."""
        try:
            while True:
                payload = await q.get()
                yield f"data: {payload}\n\n"
        except Exception:
            return


# Singleton instance — import this everywhere
broadcaster = EventBroadcaster()

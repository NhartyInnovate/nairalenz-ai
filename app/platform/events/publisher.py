import logging
from abc import ABC, abstractmethod
from typing import List, Callable, Dict, Any
from app.platform.events.base import Event

logger = logging.getLogger("event_publisher")

class BaseEventPublisher(ABC):
    @abstractmethod
    async def publish(self, event: Event) -> None:
        """
        Publish an event to interested subscribers.
        """
        pass

class InMemoryEventPublisher(BaseEventPublisher):
    """
    In-memory publisher supporting local subscriptions.
    Decoupled integration point for background task dispatch and auditable logs.
    """
    def __init__(self):
        # Maps event names to a list of asynchronous subscriber callbacks
        self._subscribers: Dict[str, List[Callable[[Event], Any]]] = {}

    def clear_subscribers(self) -> None:
        """
        Clear all registered event subscribers. Primarily used to reset state in testing.
        """
        self._subscribers.clear()

    def subscribe(self, event_name: str, callback: Callable[[Event], Any]) -> None:
        """
        Register a subscriber callback for a specific event type.
        """
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(callback)

    async def publish(self, event: Event) -> None:
        """
        Asynchronously dispatch event to all registered subscribers.
        """
        logger.info(
            f"[EVENT_PUBLISHED] ID: {event.event_id} | Name: {event.event_name} | Version: {event.event_version}",
            extra={
                "event_id": str(event.event_id),
                "event_name": event.event_name,
                "event_version": event.event_version,
                "timestamp": event.timestamp.isoformat()
            }
        )
        
        subscribers = self._subscribers.get(event.event_name, [])
        for callback in subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                # Log error but prevent one subscriber crash from blocking other executions
                logger.error(f"Subscriber callback error for event {event.event_name}: {e}")

# Import asyncio internally for callback type evaluation
import asyncio

# Singleton default instance
event_publisher = InMemoryEventPublisher()

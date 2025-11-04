from collections import defaultdict
from typing import Callable, Dict, List, Optional

from .events import Event, EventType


class OrpheusBrain:
    """
    Central orchestrator that receives telemetry events, runs advisory
    strategies, and exposes guidance to interested consumers (CLI watchdog,
    extensions, delivery pipeline).
    """

    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable[[Event], None]]] = defaultdict(list)
        self._advisors: List[Callable[[Event], Optional[List[str]]]] = []
        self._last_hints: List[str] = []

    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)

    def register_advisor(self, advisor: Callable[[Event], Optional[List[str]]]):
        if advisor not in self._advisors:
            self._advisors.append(advisor)

    def record_event(self, event: Event):
        for callback in self._subscribers[event.type]:
            try:
                callback(event)
            except Exception:
                # Avoid propagating subscriber failures
                pass
        self._last_hints = self._compute_hints(event)

    def get_last_hints(self) -> List[str]:
        return list(self._last_hints)

    def _compute_hints(self, event: Event) -> List[str]:
        hints: List[str] = []
        for advisor in self._advisors:
            try:
                advice = advisor(event)
                if advice:
                    for item in advice:
                        if item not in hints:
                            hints.append(item)
            except Exception:
                continue
        return hints


brain = OrpheusBrain()

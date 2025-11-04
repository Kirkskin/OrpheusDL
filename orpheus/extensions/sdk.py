from abc import ABC
from typing import Callable

from orpheus.services import brain, Event, EventType


class Extension(ABC):
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        brain.subscribe(event_type, callback)

    def advise(self, advisor: Callable[[Event], str]):
        def wrapper(event: Event):
            hint = advisor(event)
            if hint:
                return [hint]
            return []

        brain.register_advisor(lambda event: wrapper(event))

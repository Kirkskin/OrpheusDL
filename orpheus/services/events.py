from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Dict, Optional


class EventType(Enum):
    NETWORK = auto()
    LOGIN = auto()
    CLI = auto()
    DELIVERY = auto()


@dataclass
class Event:
    type: EventType
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class NetworkEvent(Event):
    service: Optional[str] = None
    url: Optional[str] = None
    error_code: Optional[str] = None
    message: Optional[str] = None

    def __init__(self, **kwargs):
        metadata = kwargs.pop("metadata", {})
        super().__init__(type=EventType.NETWORK, metadata=metadata)
        self.service = kwargs.get("service")
        self.url = kwargs.get("url")
        self.error_code = kwargs.get("error_code")
        self.message = kwargs.get("message")


@dataclass
class LoginEvent(Event):
    service: Optional[str] = None
    outcome: Optional[str] = None
    strategy: Optional[str] = None

    def __init__(self, **kwargs):
        metadata = kwargs.pop("metadata", {})
        super().__init__(type=EventType.LOGIN, metadata=metadata)
        self.service = kwargs.get("service")
        self.outcome = kwargs.get("outcome")
        self.strategy = kwargs.get("strategy")


@dataclass
class CLIEvent(Event):
    command: Optional[str] = None
    context: Optional[str] = None

    def __init__(self, **kwargs):
        metadata = kwargs.pop("metadata", {})
        super().__init__(type=EventType.CLI, metadata=metadata)
        self.command = kwargs.get("command")
        self.context = kwargs.get("context")

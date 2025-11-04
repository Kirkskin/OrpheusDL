from dataclasses import dataclass, field
from typing import Dict, Optional

from .registry import service_registry
from .login_strategies import LoginStrategy, get_default_strategies


@dataclass
class SessionRecord:
    service: str
    status: str = "unknown"
    strategy: Optional[str] = None
    last_error: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, SessionRecord] = {}
        self._custom_strategies: Dict[str, Dict[str, LoginStrategy]] = {}

    def get(self, service: str) -> SessionRecord:
        return self._sessions.setdefault(service, SessionRecord(service=service))

    def update_status(self, service: str, status: str, strategy: Optional[str] = None, error: Optional[str] = None):
        record = self.get(service)
        record.status = status
        record.strategy = strategy
        record.last_error = error

    def provide_credentials(self, service: str) -> Dict[str, str]:
        return service_registry.get_credentials(service)

    def register_strategy(self, service: str, strategy: LoginStrategy):
        self._custom_strategies.setdefault(service, {})[strategy.name] = strategy

    def authenticate(self, service: str, module) -> bool:
        credentials = self.provide_credentials(service)
        strategies = list(self._custom_strategies.get(service, {}).values()) or get_default_strategies(service)
        for strategy in strategies:
            if strategy.authenticate(module, credentials):
                self.update_status(service, 'authenticated', strategy=strategy.name)
                return True
        self.update_status(service, 'failed', error='all_strategies_failed')
        return False


session_manager = SessionManager()

from abc import ABC, abstractmethod
from typing import Dict, Optional

from .events import LoginEvent
from .brain import brain
from .registry import service_registry


class LoginStrategy(ABC):
    name: str

    def __init__(self, service: str):
        self.service = service

    @abstractmethod
    def is_applicable(self, credentials: Dict[str, str]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def authenticate(self, module, credentials: Dict[str, str]) -> bool:
        raise NotImplementedError


class ARLStrategy(LoginStrategy):
    name = "arl"

    def is_applicable(self, credentials: Dict[str, str]) -> bool:
        return bool(credentials.get('arl'))

    def authenticate(self, module, credentials: Dict[str, str]) -> bool:
        if not hasattr(module, 'session') or not hasattr(module.session, 'login_via_arl'):
            return False
        try:
            module.session.login_via_arl(credentials['arl'])
            brain.record_event(LoginEvent(service=self.service, outcome='success', strategy=self.name))
            return True
        except Exception as exc:
            brain.record_event(LoginEvent(service=self.service, outcome='failure', strategy=self.name, metadata={'error': str(exc)}))
            return False


class UsernamePasswordStrategy(LoginStrategy):
    name = "credentials"

    def is_applicable(self, credentials: Dict[str, str]) -> bool:
        return bool(credentials.get('username') and credentials.get('password'))

    def authenticate(self, module, credentials: Dict[str, str]) -> bool:
        if not hasattr(module, 'login'):
            return False
        try:
            module.login(credentials.get('username') or credentials.get('email'), credentials['password'])
            brain.record_event(LoginEvent(service=self.service, outcome='success', strategy=self.name))
            return True
        except Exception as exc:
            brain.record_event(LoginEvent(service=self.service, outcome='failure', strategy=self.name, metadata={'error': str(exc)}))
            return False


class TokenStrategy(LoginStrategy):
    name = "token"

    def is_applicable(self, credentials: Dict[str, str]) -> bool:
        return bool(credentials.get('auth_token'))

    def authenticate(self, module, credentials: Dict[str, str]) -> bool:
        if not hasattr(module, 'session'):
            return False
        try:
            module.session.auth_token = credentials['auth_token']
            brain.record_event(LoginEvent(service=self.service, outcome='success', strategy=self.name))
            return True
        except Exception as exc:
            brain.record_event(LoginEvent(service=self.service, outcome='failure', strategy=self.name, metadata={'error': str(exc)}))
            return False


STRATEGY_REGISTRY = [ARLStrategy, TokenStrategy, UsernamePasswordStrategy]


def get_default_strategies(service: str):
    credentials = service_registry.get_credentials(service)
    strategies = []
    for strategy_cls in STRATEGY_REGISTRY:
        strategy = strategy_cls(service)
        if strategy.is_applicable(credentials):
            strategies.append(strategy)
    return strategies

import os
from dataclasses import dataclass, field
from typing import Dict, Optional, Set


@dataclass
class ServiceInfo:
    name: str
    module: str
    capabilities: Set[str] = field(default_factory=set)
    environment_keys: Dict[str, str] = field(default_factory=dict)


class ServiceRegistry:
    def __init__(self):
        self._services: Dict[str, ServiceInfo] = {}
        self._credentials: Dict[str, Dict[str, str]] = {}

    def register(self, info: ServiceInfo):
        self._services[info.name] = info
        self._credentials.setdefault(info.name, {})

    def get_service(self, name: str) -> Optional[ServiceInfo]:
        return self._services.get(name)

    def set_credentials(self, service: str, key: str, value: str):
        self._credentials.setdefault(service, {})[key] = value

    def get_credentials(self, service: str) -> Dict[str, str]:
        creds = dict(self._credentials.get(service, {}))
        info = self._services.get(service)
        if info:
            for alias, env_key in info.environment_keys.items():
                value = os.environ.get(env_key)
                if value is not None and alias not in creds:
                    creds[alias] = value
        return creds

    def load_from_config(self, config: dict):
        self._services.clear()
        self._credentials.clear()
        modules = config.get('modules', {})
        for module_name, settings in modules.items():
            service_name = module_name.lower()
            info = ServiceInfo(
                name=service_name,
                module=module_name,
                capabilities=set(settings.keys()),
                environment_keys={key: self._env_key(service_name, key) for key in settings.keys()}
            )
            self.register(info)
            for key, value in settings.items():
                if isinstance(value, str) and value.startswith('$env:'):
                    continue  # env variables resolved at runtime
                if isinstance(value, str) and value:
                    self.set_credentials(service_name, key, value)

    @staticmethod
    def _env_key(service: str, key: str) -> str:
        return f'{service.upper()}_{key.upper()}'


service_registry = ServiceRegistry()

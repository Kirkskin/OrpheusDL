import logging
import socket
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, List, Optional

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import (
    ConnectionError,
    HTTPError,
    RequestException,
    SSLError,
    Timeout,
)
from collections import defaultdict
from urllib3.util.retry import Retry

from orpheus.services import NetworkEvent, brain


class NetworkErrorCode(Enum):
    DNS_FAILURE = auto()
    CONNECTION_TIMEOUT = auto()
    CONNECTION_FAILED = auto()
    SSL_ERROR = auto()
    HTTP_ERROR = auto()
    UNKNOWN = auto()


@dataclass
class NetworkError(Exception):
    message: str
    code: NetworkErrorCode
    original_exception: Optional[BaseException] = None
    status_code: Optional[int] = None
    url: Optional[str] = None
    hints: List[str] = field(default_factory=list)

    def __str__(self):
        return self.message


class NetworkManager:
    def __init__(self):
        self.session = self._create_session()
        self._advisors: List[Callable[[NetworkError], List[str]]] = []
        self._failures = defaultdict(int)
        self.offline_mode = False

    @staticmethod
    def _create_session() -> requests.Session:
        session = requests.Session()

        retry_strategy = Retry(
            total=5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"],
            backoff_factor=0.4,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.verify = True
        return session

    def configure(self, allow_insecure_requests: bool):
        self.session.verify = not allow_insecure_requests
        if allow_insecure_requests:
            requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]

    def register_advisor(self, advisor: Callable[[NetworkError], List[str]]):
        if advisor not in self._advisors:
            self._advisors.append(advisor)

    def _enrich_error(self, error: NetworkError) -> NetworkError:
        for advisor in self._advisors:
            try:
                hints = advisor(error) or []
                for hint in hints:
                    if hint not in error.hints:
                        error.hints.append(hint)
            except Exception:  # pragma: no cover - advisor failures shouldn't break flow
                logging.debug("Network advisor failed", exc_info=True)
        return error

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        if self.offline_mode or kwargs.get('simulate_offline'):
            error = NetworkError(
                message=f'Offline mode enabled, cannot reach {url}',
                code=NetworkErrorCode.CONNECTION_FAILED,
                url=url
            )
            brain.record_event(NetworkEvent(service=kwargs.get('service'), url=url, error_code=error.code.name, message=error.message))
            raise error
        try:
            response = self.session.request(method=method, url=url, **kwargs)
            response.raise_for_status()
            self._failures[url] = 0
            return response
        except SSLError as exc:
            error = NetworkError(
                message=f"SSL error while contacting {url}: {exc}",
                code=NetworkErrorCode.SSL_ERROR,
                original_exception=exc,
                url=url,
            )
        except Timeout as exc:
            error = NetworkError(
                message=f"Request to {url} timed out",
                code=NetworkErrorCode.CONNECTION_TIMEOUT,
                original_exception=exc,
                url=url,
            )
        except ConnectionError as exc:
            code = NetworkErrorCode.CONNECTION_FAILED
            if self._is_dns_error(exc):
                code = NetworkErrorCode.DNS_FAILURE
            error = NetworkError(
                message=f"Unable to reach {url}: {exc}",
                code=code,
                original_exception=exc,
                url=url,
            )
        except HTTPError as exc:
            response = getattr(exc, 'response', None)
            if response is None:
                for arg in getattr(exc, 'args', []):
                    if isinstance(arg, requests.Response):
                        response = arg
                        break
            status = response.status_code if response else None
            error = NetworkError(
                message=f"HTTP error contacting {url}: {status}",
                code=NetworkErrorCode.HTTP_ERROR,
                original_exception=exc,
                status_code=status,
                url=url,
            )
        except RequestException as exc:
            error = NetworkError(
                message=f"Unhandled request error contacting {url}: {exc}",
                code=NetworkErrorCode.UNKNOWN,
                original_exception=exc,
                url=url,
            )
        network_event = NetworkEvent(
            service=kwargs.get("service"),
            url=url,
            error_code=error.code.name,
            message=error.message,
        )
        brain.record_event(network_event)
        self._failures[url] += 1
        if self._failures[url] >= 3:
            error.hints.append('Repeated failures detected. Circuit breaker activated for this endpoint.')
        self._enrich_error(error)
        raise error

    @staticmethod
    def _is_dns_error(exc: ConnectionError) -> bool:
        candidates = [exc.__cause__, exc.__context__, exc]
        for candidate in filter(None, candidates):
            if isinstance(candidate, socket.gaierror):
                return True
            if isinstance(candidate, ConnectionError) and candidate is not exc:
                if NetworkManager._is_dns_error(candidate):
                    return True
        # inspect arguments for embedded gaierror
        for arg in getattr(exc, "args", []):
            if isinstance(arg, socket.gaierror):
                return True
        message = str(exc).lower()
        return 'name or service not known' in message or 'gaierror' in message


network_manager = NetworkManager()


def register_network_advisor(advisor: Callable[[NetworkError], List[str]]):
    network_manager.register_advisor(advisor)


def set_offline_mode(enabled: bool):
    network_manager.offline_mode = enabled

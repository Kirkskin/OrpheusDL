from utils.models import ExtensionInformation
from utils.network import NetworkError, NetworkErrorCode, register_network_advisor
from orpheus.services import brain, Event, EventType


extension_settings = ExtensionInformation(
    extension_type='network_ai',
    settings={}
)


class OrpheusExtension:
    def __init__(self, settings: dict):
        register_network_advisor(self.suggest)
        brain.register_advisor(self._brain_advisor)

    @staticmethod
    def suggest(error: NetworkError):
        hints = []
        if error.code is NetworkErrorCode.DNS_FAILURE:
            hints.append('Verify internet connectivity or disable VPN/proxy blocking DNS resolution.')
            hints.append('Try switching to a connection with direct access to the service region.')
        elif error.code is NetworkErrorCode.CONNECTION_TIMEOUT:
            hints.append('Service took too long to respond; consider retrying shortly.')
            hints.append('Check if the service is rate limiting or throttling connections.')
        elif error.code is NetworkErrorCode.HTTP_ERROR and error.status_code:
            if error.status_code == 401:
                hints.append('Authentication failed; refresh credentials or session tokens.')
            elif error.status_code in {403, 451}:
                hints.append('Access denied. Ensure the account has permission and is in a supported region.')
            elif error.status_code == 429:
                hints.append('Too many requests; wait before retrying or reduce concurrency.')
            else:
                hints.append('Unexpected HTTP error from service; review logs for full response.')
        elif error.code is NetworkErrorCode.SSL_ERROR:
            hints.append('SSL handshake failed. Ensure system clock is correct and avoid interception proxies.')
        elif error.code is NetworkErrorCode.CONNECTION_FAILED:
            hints.append('Server unreachable. Validate firewall settings and that the host is online.')
        else:
            hints.append('Encountered an unknown network issue; enable debug logs for more detail.')
        return hints

    @staticmethod
    def _brain_advisor(event: Event):
        hints = []
        if event.type is EventType.LOGIN:
            outcome = getattr(event, 'outcome', None)
            service = getattr(event, 'service', 'service')
            if outcome == 'failure':
                hints.append(f'{service}: login failed. Verify credentials or refresh session tokens.')
            elif outcome == 'success':
                hints.append(f'{service}: login refreshed successfully.')
        return hints

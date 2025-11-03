import socket
import unittest
from unittest.mock import patch

import requests

from utils.network import NetworkError, NetworkErrorCode, network_manager


class NetworkManagerTests(unittest.TestCase):
    def setUp(self):
        self._original_advisors = list(network_manager._advisors)  # type: ignore[attr-defined]

    def tearDown(self):
        network_manager._advisors = self._original_advisors  # type: ignore[attr-defined]

    def test_dns_failure_classification(self):
        def advisor(error: NetworkError):
            if error.code is NetworkErrorCode.DNS_FAILURE:
                return ['DNS hint']
            return []

        network_manager.register_advisor(advisor)
        dns_exception = requests.exceptions.ConnectionError(socket.gaierror(-2, 'Name or service not known'))
        with patch.object(network_manager.session, 'request', side_effect=dns_exception):
            with self.assertRaises(NetworkError) as ctx:
                network_manager.request('GET', 'https://example.invalid')
        error = ctx.exception
        self.assertEqual(error.code, NetworkErrorCode.DNS_FAILURE)
        self.assertIn('DNS hint', error.hints)

    def test_http_error_classification(self):
        response = requests.Response()
        response.status_code = 403

        def raise_http(*args, **kwargs):
            exc = requests.exceptions.HTTPError(response=response)
            raise exc

        with patch.object(network_manager.session, 'request', side_effect=raise_http):
            with self.assertRaises(NetworkError) as ctx:
                network_manager.request('GET', 'https://example.com/resource')
        error = ctx.exception
        self.assertEqual(error.code, NetworkErrorCode.HTTP_ERROR)


if __name__ == '__main__':
    unittest.main()

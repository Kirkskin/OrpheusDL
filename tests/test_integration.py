import unittest
from unittest.mock import patch, MagicMock

from orpheus.delivery import delivery_pipeline
from utils.network import network_manager


class DownloadIntegrationTests(unittest.TestCase):
    def test_delivery_events(self):
        job_id = delivery_pipeline.begin_job('testservice', 'track', '123')
        delivery_pipeline.complete_job(job_id, 'testservice', True)
        self.assertTrue(job_id.startswith('testservice-track-'))

    @patch('utils.network.network_manager.request')
    def test_network_offline(self, request_mock):
        request_mock.side_effect = Exception('forced')
        with self.assertRaises(Exception):
            network_manager.request('GET', 'https://example.com')


if __name__ == '__main__':
    unittest.main()

import unittest

from orpheus.services import service_registry, session_manager


class ServiceRegistryTests(unittest.TestCase):
    def setUp(self):
        self._services_backup = dict(service_registry._services)
        self._credentials_backup = dict(service_registry._credentials)

    def tearDown(self):
        service_registry._services = self._services_backup
        service_registry._credentials = self._credentials_backup

    def test_load_from_config(self):
        config = {
            "modules": {
                "deezer": {
                    "client_id": "123",
                    "client_secret": "$env:DEEZER_CLIENT_SECRET",
                }
            }
        }
        service_registry.load_from_config(config)
        info = service_registry.get_service("deezer")
        self.assertIsNotNone(info)
        creds = service_registry.get_credentials("deezer")
        self.assertEqual(creds.get("client_id"), "123")
        # env-based credential should be absent if not set
        self.assertNotIn("client_secret", creds)


class SessionManagerTests(unittest.TestCase):
    def test_session_updates(self):
        session_manager.update_status("deezer", "authenticated", strategy="arl")
        session = session_manager.get("deezer")
        self.assertEqual(session.status, "authenticated")
        self.assertEqual(session.strategy, "arl")


if __name__ == "__main__":
    unittest.main()

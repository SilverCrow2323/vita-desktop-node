import ssl
import tempfile
import unittest
import uuid
from pathlib import Path

from vdn.security.pairing import PairingStore
from vdn.services.host_service import HostService


class HostServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = PairingStore(Path(self.tmp.name))
        self.info = {
            "node_id": "host-uuid",
            "capabilities": {"node.info": True, "actions.execution": False},
        }
        self.service = HostService(self.store, lambda: self.info)
        self.device_id = str(uuid.uuid4())

    def tearDown(self):
        self.tmp.cleanup()

    def _auth(self):
        code = self.store.open_pairing_window()["code"]
        request = self.store.request_pairing(
            code=code, device_id=self.device_id, device_name="Vita",
            requested_permissions=["node.info"],
        )
        credential = self.store.approve_request(request["request_id"])["credential"]
        return {"device_id": self.device_id, "credential": credential}

    def _request(self, method, params):
        return {"protocol": "VDN2", "version": 2, "type": "request",
                "id": "test-req", "method": method, "params": params}

    def test_node_info_requires_authentication(self):
        result = self.service.dispatch(self._request("node.info", {}))
        self.assertFalse(result["ok"])

    def test_authenticated_read_only_node_info(self):
        result = self.service.dispatch(self._request("node.info", {"auth": self._auth()}))
        self.assertTrue(result["ok"])
        self.assertEqual(result["result"]["node_id"], "host-uuid")
        self.assertEqual(result["result"]["authenticated_device"], self.device_id)

    def test_capabilities_are_read_only_and_actions_not_exposed(self):
        result = self.service.dispatch(self._request("node.capabilities", {"auth": self._auth()}))
        self.assertTrue(result["ok"])
        self.assertFalse(result["result"]["capabilities"]["actions.execution"])
        denied = self.service.dispatch(self._request("actions.invoke", {"auth": self._auth()}))
        self.assertFalse(denied["ok"])
        self.assertEqual(denied["error"]["code"], "method_not_found")

    def test_pairing_request_creates_pending_only(self):
        code = self.store.open_pairing_window()["code"]
        result = self.service.dispatch(self._request("pairing.request", {
            "code": code, "device_id": self.device_id, "device_name": "Vita",
            "requested_permissions": ["node.info"],
        }))
        self.assertTrue(result["ok"])
        self.assertEqual(result["result"]["status"], "pending_host_approval")
        self.assertEqual(self.store.paired_devices(), [])



class HostServiceTLSGuardTests(unittest.IsolatedAsyncioTestCase):
    async def test_listener_rejects_client_tls_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = PairingStore(Path(tmp))
            service = HostService(store, lambda: {})
            context = ssl.create_default_context()
            with self.assertRaisesRegex(ValueError, "PROTOCOL_TLS_SERVER"):
                await service.start("127.0.0.1", 0, tls_context=context)
            await service.close()


if __name__ == "__main__":
    unittest.main()

import hashlib
import json
import tempfile
import unittest
import uuid
from pathlib import Path

from vdn.security.pairing import PairingError, PairingStore


class PairingStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = PairingStore(Path(self.tmp.name), credential_ttl=3600)
        self.device_id = str(uuid.uuid4())

    def tearDown(self):
        self.tmp.cleanup()

    def _pending(self):
        window = self.store.open_pairing_window()
        result = self.store.request_pairing(
            code=window["code"], device_id=self.device_id,
            device_name="PS Vita test", requested_permissions=["node.info", "files.list"],
        )
        return result["request_id"]

    def test_pairing_code_is_single_use_and_requires_local_approval(self):
        window = self.store.open_pairing_window()
        pending = self.store.request_pairing(
            code=window["code"], device_id=self.device_id,
            device_name="Vita", requested_permissions=["node.info"],
        )
        self.assertEqual(pending["status"], "pending_host_approval")
        self.assertEqual(len(self.store.pending_requests()), 1)
        with self.assertRaisesRegex(PairingError, "closed"):
            self.store.request_pairing(
                code=window["code"], device_id=str(uuid.uuid4()),
                device_name="Second", requested_permissions=["node.info"],
            )
        self.assertEqual(self.store.paired_devices(), [])

    def test_approval_returns_secret_once_and_only_hash_is_persisted(self):
        request_id = self._pending()
        result = self.store.approve_request(request_id, permissions=["node.info"])
        raw = self.store.path.read_text(encoding="utf-8")
        self.assertNotIn(result["credential"], raw)
        self.assertEqual(
            self.store.authenticate(device_id=self.device_id,
                                    credential=result["credential"],
                                    required_permission="node.info")["device_id"],
            self.device_id,
        )
        self.assertNotIn("files.list", self.store.paired_devices()[0]["permissions"])

    def test_unapproved_or_unrequested_permissions_cannot_be_granted(self):
        request_id = self._pending()
        with self.assertRaisesRegex(PairingError, "requested"):
            self.store.approve_request(request_id, permissions=["terminal.execute"])

    def test_invalid_code_attempts_close_window_after_five(self):
        window = self.store.open_pairing_window()
        for _ in range(5):
            with self.assertRaises(PairingError):
                self.store.request_pairing(
                    code="wrong-code", device_id=self.device_id,
                    device_name="Vita", requested_permissions=["node.info"],
                )
        with self.assertRaisesRegex(PairingError, "closed"):
            self.store.request_pairing(
                code=window["code"], device_id=self.device_id,
                device_name="Vita", requested_permissions=["node.info"],
            )

    def test_revocation_and_permission_denial(self):
        request_id = self._pending()
        credential = self.store.approve_request(request_id)["credential"]
        with self.assertRaisesRegex(PairingError, "lacks"):
            self.store.authenticate(device_id=self.device_id, credential=credential,
                                    required_permission="terminal.execute")
        self.store.revoke_device(self.device_id)
        with self.assertRaisesRegex(PairingError, "not paired"):
            self.store.authenticate(device_id=self.device_id, credential=credential,
                                    required_permission="node.info")

    def test_credentials_survive_restart_but_plaintext_does_not(self):
        request_id = self._pending()
        credential = self.store.approve_request(request_id)["credential"]
        restarted = PairingStore(Path(self.tmp.name), credential_ttl=3600)
        self.assertEqual(
            restarted.authenticate(device_id=self.device_id, credential=credential,
                                   required_permission="node.info")["device_id"],
            self.device_id,
        )
        self.assertEqual(hashlib.sha256(credential.encode()).hexdigest(),
                         json.loads(restarted.path.read_text())["devices"][self.device_id]["credential_hash"])


if __name__ == "__main__":
    unittest.main()

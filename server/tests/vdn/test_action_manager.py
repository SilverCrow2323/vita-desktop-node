from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from vdn.action_manager import ActionError, ActionManager


class ActionManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.manager = ActionManager(Path(self.temp.name))

    def test_approval_confirmation_and_execution(self):
        m=self.manager
        p=m.add_custom_action(action_id="test.echo",name="Echo",argv=[sys.executable,"-c","print('ok')"])
        self.assertFalse(p["approved"]); self.assertFalse(p["enabled"]); self.assertNotIn("argv",p)
        with self.assertRaisesRegex(ActionError,"approved"): m.run("test.echo",confirmed=True)
        m.approve("test.echo")
        with self.assertRaisesRegex(ActionError,"confirmation"): m.run("test.echo")
        result=m.run("test.echo",confirmed=True)
        self.assertEqual(result["returncode"],0); self.assertEqual(result["stdout"].strip(),"ok")

    def test_persistence_and_public_argv_secrecy(self):
        m=self.manager
        m.add_custom_action(action_id="test.persist",name="Persist",argv=[sys.executable,"--version"])
        n=ActionManager(Path(self.temp.name))
        self.assertNotIn("argv",n.public_catalog()[0])
        stored=json.loads(n.state_file.read_text())
        self.assertEqual(stored["test.persist"]["argv"][0],sys.executable)

    def test_scanned_app_starts_disabled(self):
        app=SimpleNamespace(action_id="linux.desktop.abcdef1234567890",name="Editor",
            categories=("Utility",),icon="editor",platform="linux",launch_argv=(sys.executable,"--version"))
        p=self.manager.register_application(app)
        self.assertFalse(p["approved"]); self.assertFalse(p["enabled"]); self.assertNotIn("argv",p)

    def test_shell_and_privilege_escalation_blocked(self):
        commands=[["bash","-c","echo unsafe"],["sh","-c","id"],["sudo","true"],
                  ["pkexec","true"],["powershell","-Command","x"]]
        for index,argv in enumerate(commands):
            with self.subTest(argv=argv), self.assertRaises(ActionError):
                self.manager.add_custom_action(action_id=f"test.block{index}",name="Blocked",argv=argv)

    def test_enable_requires_approval_and_revoke(self):
        m=self.manager
        m.add_custom_action(action_id="test.switch",name="Switch",argv=[sys.executable,"--version"])
        with self.assertRaisesRegex(ActionError,"approved"): m.set_enabled("test.switch",True)
        m.approve("test.switch"); m.set_enabled("test.switch",False); m.revoke("test.switch")
        with self.assertRaisesRegex(ActionError,"unknown"): m.public_action("test.switch")

    def test_timeout_and_extra_args_validation(self):
        m=self.manager
        m.add_custom_action(action_id="test.args",name="Args",argv=[sys.executable,"--version"])
        m.approve("test.args")
        with self.assertRaisesRegex(ActionError,"timeout"): m.run("test.args",confirmed=True,timeout=999)
        with self.assertRaisesRegex(ActionError,"extra arguments"): m.run("test.args",confirmed=True,extra_args=["x"]*17)

    def test_catalog_refresh_preserves_approval_only_when_command_is_unchanged(self):
        m=self.manager
        def app(argv):
            return SimpleNamespace(action_id="linux.desktop.abcdef1234567890",name="Editor",
                categories=("Utility",),icon="editor",platform="linux",launch_argv=tuple(argv))
        m.register_application(app([sys.executable,"--version"]))
        m.approve("linux.desktop.abcdef1234567890")
        m.register_application(app([sys.executable,"--version"]))
        self.assertTrue(m.public_action("linux.desktop.abcdef1234567890")["enabled"])
        m.register_application(app([sys.executable,"-c","print('changed')"]))
        refreshed=m.public_action("linux.desktop.abcdef1234567890")
        self.assertFalse(refreshed["approved"]); self.assertFalse(refreshed["enabled"])


    def test_launch_returns_pid_without_waiting_for_desktop_process_exit(self):
        m = self.manager
        m.add_custom_action(
            action_id="test.launch",
            name="Background launch",
            argv=[sys.executable, "-c", "import time; time.sleep(0.25)"],
        )
        m.approve("test.launch")
        result = m.launch("test.launch", confirmed=True)
        self.assertTrue(result["started"])
        self.assertIsInstance(result["pid"], int)
        self.assertGreater(result["pid"], 0)
        audit = m.audit_file.read_text(encoding="utf-8")
        self.assertIn('"event": "launched"', audit)
        self.assertIn('"pid":', audit)

    def test_launch_requires_approval_and_confirmation(self):
        m = self.manager
        m.add_custom_action(
            action_id="test.launchguard",
            name="Guarded launch",
            argv=[sys.executable, "--version"],
        )
        with self.assertRaisesRegex(ActionError, "approved"):
            m.launch("test.launchguard", confirmed=True)
        m.approve("test.launchguard")
        with self.assertRaisesRegex(ActionError, "confirmation"):
            m.launch("test.launchguard")

    def test_local_approval_details_are_not_in_public_catalog(self):
        m = self.manager
        m.add_custom_action(
            action_id="test.details",
            name="Reviewed action",
            argv=[sys.executable, "--version"],
        )
        details = m.local_details("test.details")
        self.assertEqual(details["argv"], [sys.executable, "--version"])
        self.assertNotIn("argv", m.public_action("test.details"))
        self.assertNotIn("argv", m.public_catalog()[0])


if __name__ == "__main__":
    unittest.main()

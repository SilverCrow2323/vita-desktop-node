import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import vitamon_gui


class LinuxHostIntegrationTests(unittest.TestCase):
    def test_xdg_config_location(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmp}, clear=False), patch.object(vitamon_gui.sys, "platform", "linux"):
                self.assertEqual(vitamon_gui.config_path(), os.path.join(tmp, "VitaMon", "config.json"))

    def test_linux_autostart_create_and_remove(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {"XDG_CONFIG_HOME": tmp}
            with patch.dict(os.environ, env, clear=False), patch.object(vitamon_gui.sys, "platform", "linux"):
                self.assertFalse(vitamon_gui.get_run_at_login())
                vitamon_gui.set_run_at_login(True)
                path = Path(tmp) / "autostart" / "vitamon.desktop"
                self.assertTrue(path.is_file())
                contents = path.read_text(encoding="utf-8")
                self.assertIn("[Desktop Entry]", contents)
                self.assertIn("--start --minimized", contents)
                self.assertTrue(vitamon_gui.get_run_at_login())
                vitamon_gui.set_run_at_login(False)
                self.assertFalse(path.exists())

    def test_linux_single_instance_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"XDG_RUNTIME_DIR": tmp}, clear=False), patch.object(vitamon_gui.sys, "platform", "linux"):
                self.assertFalse(vitamon_gui.already_running())
                self.assertTrue(vitamon_gui.already_running())
                del vitamon_gui.already_running.handle
                self.assertFalse(vitamon_gui.already_running())


if __name__ == "__main__":
    unittest.main()

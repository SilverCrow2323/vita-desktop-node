import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from vdn.config import AppPaths, load_json, save_json
from vdn.node import build_node_info, load_or_create_node_id


class ConfigTests(unittest.TestCase):
    def test_xdg_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "XDG_CONFIG_HOME": str(Path(tmp) / "config"),
                "XDG_STATE_HOME": str(Path(tmp) / "state"),
                "XDG_CACHE_HOME": str(Path(tmp) / "cache"),
            }
            with patch.dict(os.environ, env, clear=False):
                paths = AppPaths.discover()
            self.assertEqual(paths.config, Path(tmp) / "config" / "vitadesktopnode")
            self.assertEqual(paths.logs, Path(tmp) / "state" / "vitadesktopnode" / "logs")

    def test_atomic_json_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            save_json(path, {"language": "it", "enabled": True})
            self.assertEqual(load_json(path), {"language": "it", "enabled": True})

    def test_invalid_json_uses_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.json"
            path.write_text("{", encoding="utf-8")
            self.assertEqual(load_json(path, default={"safe": True}), {"safe": True})

    def test_node_id_persists_and_is_uuid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = AppPaths(root / "config", root / "state", root / "cache", root / "logs")
            first = load_or_create_node_id(paths)
            second = load_or_create_node_id(paths)
            self.assertEqual(first, second)
            self.assertEqual(len(first), 36)

    def test_unimplemented_features_are_not_advertised(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = AppPaths(root / "config", root / "state", root / "cache", root / "logs")
            info = build_node_info(paths)
            self.assertTrue(info["capabilities"]["vdn2.framing"])
            self.assertFalse(info["capabilities"]["terminal.pty"])
            self.assertFalse(info["capabilities"]["display.extended"])


if __name__ == "__main__":
    unittest.main()

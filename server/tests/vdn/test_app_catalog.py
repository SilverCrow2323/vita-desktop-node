import tempfile
import unittest
from pathlib import Path

from vdn.app_catalog import parse_desktop_file, scan_linux_applications, validate_custom_action


class ApplicationCatalogTests(unittest.TestCase):
    def write_entry(self, root, filename, content):
        path = root / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_scans_visible_desktop_entries_without_exposing_exec(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_entry(root, "browser.desktop", """[Desktop Entry]
Type=Application
Name=Example Browser
Exec=firefox --new-window %u
Icon=firefox
Categories=Network;WebBrowser;
""")
            self.write_entry(root, "hidden.desktop", """[Desktop Entry]
Type=Application
Name=Hidden
Exec=hidden
NoDisplay=true
""")
            apps = scan_linux_applications([root])
            self.assertEqual([app.name for app in apps], ["Example Browser"])
            public = apps[0].public_dict()
            self.assertEqual(public["icon"], "firefox")
            self.assertEqual(apps[0].launch_argv, ("firefox", "--new-window"))
            self.assertNotIn("Exec", public)
            self.assertNotIn("argv", public)
            self.assertTrue(str(public["action_id"]).startswith("linux.desktop."))

    def test_ignores_invalid_and_non_application_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad = self.write_entry(root, "bad.desktop", "[Desktop Entry]\nExec=\"")
            other = self.write_entry(root, "link.desktop", """[Desktop Entry]
Type=Link
Name=Website
URL=https://example.com
""")
            self.assertIsNone(parse_desktop_file(bad, root))
            self.assertIsNone(parse_desktop_file(other, root))

    def test_vita_custom_action_is_inert_until_host_approval(self):
        action = validate_custom_action({
            "action_id": "custom.launch.notes",
            "name": "Open notes",
            "categories": ["Productivity"],
            "argv": ["/usr/bin/notes", "--new"],
        })
        self.assertFalse(action["enabled"])
        self.assertTrue(action["requires_confirmation"])
        self.assertEqual(action["origin"], "vita-proposal")

    def test_rejects_shell_string_instead_of_argv(self):
        with self.assertRaises(ValueError):
            validate_custom_action({
                "action_id": "custom.bad.command",
                "name": "Unsafe",
                "argv": "rm -rf /",
            })


if __name__ == "__main__":
    unittest.main()

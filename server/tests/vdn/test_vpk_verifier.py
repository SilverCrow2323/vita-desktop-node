import struct
import tempfile
import unittest
import zipfile
from pathlib import Path

from vita.tools.verify_vpk import REQUIRED_FILES, parse_sfo, verify_vpk


def make_sfo(title_id="VDN000001", title="Vita Desktop Node", app_ver="00.10"):
    fields = [
        ("TITLE", title),
        ("TITLE_ID", title_id),
        ("APP_VER", app_ver),
    ]
    keys = b""
    values = b""
    entries = []
    for key, value in fields:
        key_bytes = key.encode("ascii") + b"\0"
        value_bytes = value.encode("utf-8") + b"\0"
        entries.append((len(keys), len(values), len(value_bytes)))
        keys += key_bytes
        values += value_bytes
    key_offset = 20 + 16 * len(fields)
    data_offset = key_offset + len(keys)
    header = b"\0PSF" + struct.pack("<4I", 0x00000101, key_offset, data_offset, len(fields))
    index = b"".join(
        struct.pack("<HHIII", key_rel, 0x0204, value_len, value_len, value_rel)
        for key_rel, value_rel, value_len in entries
    )
    return header + index + keys + values


class VpkVerifierTests(unittest.TestCase):
    def make_vpk(self, path, title_id="VDN000001", omit=None, overrides=None):
        with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as archive:
            for name in REQUIRED_FILES:
                if name == omit:
                    continue
                default = (
                    make_sfo(title_id)
                    if name == "sce_sys/param.sfo"
                    else (b"\x89PNG\r\n\x1a\n" + b"x" * 300
                          if name.endswith(".png")
                          else b'<?xml version="1.0"?><livearea/>')
                )
                archive.writestr(name, (overrides or {}).get(name, default))

    def test_valid_package_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "preview.vpk"
            self.make_vpk(path)
            info = verify_vpk(path)
            self.assertEqual(info["TITLE_ID"], "VDN000001")
            self.assertEqual(info["TITLE"], "Vita Desktop Node")
            self.assertEqual(info["APP_VER"], "00.10")

    def test_rejects_wrong_title_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wrong.vpk"
            self.make_vpk(path, title_id="VMON00001")
            with self.assertRaisesRegex(ValueError, "TITLE_ID mismatch"):
                verify_vpk(path)

    def test_rejects_missing_required_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "incomplete.vpk"
            self.make_vpk(path, omit="eboot.bin")
            with self.assertRaisesRegex(ValueError, "missing package entries"):
                verify_vpk(path)


    def test_rejects_invalid_livearea_xml(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad-livearea.vpk"
            self.make_vpk(path, overrides={
                "sce_sys/livearea/contents/template.xml": b"<broken"
            })
            with self.assertRaisesRegex(ValueError, "invalid LiveArea template XML"):
                verify_vpk(path)

    def test_rejects_invalid_png_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad-png.vpk"
            self.make_vpk(path, overrides={"sce_sys/icon0.png": b"not a png"})
            with self.assertRaisesRegex(ValueError, "invalid PNG signature"):
                verify_vpk(path)

    def test_rejects_invalid_sfo(self):
        with self.assertRaisesRegex(ValueError, "invalid PARAM.SFO"):
            parse_sfo(b"not-a-param-sfo")


if __name__ == "__main__":
    unittest.main()

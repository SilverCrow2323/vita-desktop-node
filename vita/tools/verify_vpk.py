#!/usr/bin/env python3
"""Validate the Vita Desktop Node VPK container and its PARAM.SFO identity."""
from __future__ import annotations

import argparse
import struct
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

EXPECTED_TITLE_ID = "VDN000001"
EXPECTED_TITLE = "Vita Desktop Node"
REQUIRED_FILES = (
    "eboot.bin",
    "sce_sys/param.sfo",
    "sce_sys/icon0.png",
    "sce_sys/livearea/contents/bg.png",
    "sce_sys/livearea/contents/startup.png",
    "sce_sys/livearea/contents/template.xml",
)


def parse_sfo(data: bytes) -> dict[str, str]:
    if len(data) < 20 or data[:4] != b"\x00PSF":
        raise ValueError("invalid PARAM.SFO magic/header")
    _, key_offset, data_offset, count = struct.unpack_from("<4I", data, 4)
    if count > 4096 or 20 + count * 16 > len(data):
        raise ValueError("invalid PARAM.SFO index table")
    values: dict[str, str] = {}
    for index in range(count):
        entry = 20 + index * 16
        key_rel, fmt, length, max_length, value_rel = struct.unpack_from("<HHIII", data, entry)
        key_pos = key_offset + key_rel
        value_pos = data_offset + value_rel
        if key_pos >= len(data) or value_pos + length > len(data) or length > max_length:
            raise ValueError("PARAM.SFO entry points outside the file")
        key_end = data.find(b"\0", key_pos)
        if key_end < 0:
            raise ValueError("unterminated PARAM.SFO key")
        key = data[key_pos:key_end].decode("utf-8")
        raw = data[value_pos:value_pos + length]
        if fmt in (0x0204, 0x0004):
            value = raw.split(b"\0", 1)[0].decode("utf-8", errors="strict")
        else:
            value = raw.hex()
        values[key] = value
    return values


def verify_vpk(path: Path) -> dict[str, str]:
    if not path.is_file() or path.stat().st_size < 1024:
        raise ValueError("VPK is missing or unexpectedly small")
    if not zipfile.is_zipfile(path):
        raise ValueError("VPK is not a valid ZIP-compatible package")
    with zipfile.ZipFile(path) as archive:
        entries = archive.namelist()
        names = set(entries)
        if len(entries) != len(names):
            raise ValueError("VPK contains duplicate archive entries")
        corrupt = archive.testzip()
        if corrupt is not None:
            raise ValueError(f"VPK CRC check failed for {corrupt}")
        missing = [name for name in REQUIRED_FILES if name not in names]
        if missing:
            raise ValueError("missing package entries: " + ", ".join(missing))
        for image_name in (
            "sce_sys/icon0.png",
            "sce_sys/livearea/contents/bg.png",
            "sce_sys/livearea/contents/startup.png",
        ):
            if not archive.read(image_name).startswith(b"\x89PNG\r\n\x1a\n"):
                raise ValueError(f"invalid PNG signature: {image_name}")
        try:
            root = ET.fromstring(archive.read("sce_sys/livearea/contents/template.xml"))
        except ET.ParseError as exc:
            raise ValueError(f"invalid LiveArea template XML: {exc}") from exc
        if root.tag != "livearea":
            raise ValueError("LiveArea template root element must be <livearea>")
        info = parse_sfo(archive.read("sce_sys/param.sfo"))
        if info.get("TITLE_ID") != EXPECTED_TITLE_ID:
            raise ValueError(f"TITLE_ID mismatch: {info.get('TITLE_ID')!r}")
        if info.get("TITLE") != EXPECTED_TITLE:
            raise ValueError(f"TITLE mismatch: {info.get('TITLE')!r}")
        if info.get("APP_VER") != "00.10":
            raise ValueError(f"APP_VER mismatch: {info.get('APP_VER')!r}")
        return info


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vpk", type=Path)
    args = parser.parse_args()
    try:
        info = verify_vpk(args.vpk)
    except (OSError, ValueError, zipfile.BadZipFile, UnicodeError) as exc:
        print(f"VPK validation FAILED: {exc}", file=sys.stderr)
        return 1
    print("VPK validation OK")
    print(f"Title: {info['TITLE']}")
    print(f"Title ID: {info['TITLE_ID']}")
    print(f"App version: {info['APP_VER']}")
    print(f"Package size: {args.vpk.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

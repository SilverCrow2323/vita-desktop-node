"""Minimal Vita Desktop Node host-core entry point (no network listener yet)."""
from __future__ import annotations

import argparse

from .config import AppPaths
from .node import render_node_info


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Vita Desktop Node host core")
    parser.add_argument("--print-info", action="store_true",
                        help="print local node identity and implemented capabilities")
    parser.add_argument("--print-config-dir", action="store_true",
                        help="print the per-user configuration directory")
    args = parser.parse_args(argv)

    paths = AppPaths.discover()
    if args.print_config_dir:
        print(paths.config)
        return 0
    if args.print_info or not (args.print_config_dir or args.print_info):
        print(render_node_info(paths))
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

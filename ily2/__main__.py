import argparse
import os
import sys

from ily2 import __version__
from ily2.lib.output import console, error


def run() -> None:
    parser = argparse.ArgumentParser(
        prog="ily2",
        description="ILY2 - guided Gentoo Linux installer (archinstall-inspired)",
    )
    parser.add_argument(
        "--script",
        default="guided",
        help="Which install script to run (default: guided)",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to a JSON config file to pre-fill / automate answers",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print every command instead of executing it (safe to test with)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"ily2 {__version__}",
    )
    args = parser.parse_args()

    if os.geteuid() != 0 and not args.dry_run:
        error("ILY2 root olarak çalıştırılmalı (sudo veya canlı ortamda zaten root'sunuzdur).")
        sys.exit(1)

    if args.script == "guided":
        from ily2.scripts.guided import main as guided_main

        guided_main(config_path=args.config, dry_run=args.dry_run)
    else:
        error(f"Bilinmeyen script: {args.script}")
        sys.exit(1)


if __name__ == "__main__":
    run()

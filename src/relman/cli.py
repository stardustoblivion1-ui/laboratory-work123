"""Консольный интерфейс relman."""
from __future__ import annotations

import argparse
import sys

from .release import check_tag, register, register_bump
from .version import VersionError, read_version


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="relman")
    p.add_argument("--pyproject", default="pyproject.toml")
    p.add_argument("--changelog", default="CHANGELOG.md")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show")
    b = sub.add_parser("bump")
    b.add_argument("part", choices=["major", "minor", "patch"])
    b.add_argument("-m", "--message", action="append", required=True)
    s = sub.add_parser("set")
    s.add_argument("version")
    s.add_argument("-m", "--message", action="append", required=True)
    sub.add_parser("check-tag").add_argument("tag", nargs="?")
    return p


def run(argv=None) -> int:
    a = build_parser().parse_args(argv)
    try:
        if a.cmd == "show":
            print(read_version(a.pyproject))
        elif a.cmd == "bump":
            print(register_bump(a.pyproject, a.changelog, a.part, a.message))
        elif a.cmd == "set":
            print(register(a.pyproject, a.changelog, a.version, a.message))
        elif a.cmd == "check-tag":
            print(f"OK: тег {a.tag} соответствует версии {check_tag(a.tag, a.pyproject)}")
    except VersionError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1
    return 0


def main() -> None:
    sys.exit(run())

"""Консольный интерфейс fvm."""
from __future__ import annotations

import argparse
import sys

from .compare import diff_lines
from .storage import VersionError, VersionStore


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="fvm", description="Менеджер версий текстовых документов")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("save", help="сохранить версию")
    s.add_argument("file")
    s.add_argument("-m", "--message", default="")
    sub.add_parser("list", help="список версий").add_argument("file")
    r = sub.add_parser("restore", help="восстановить версию")
    r.add_argument("file")
    r.add_argument("version", type=int)
    sh = sub.add_parser("show", help="показать версию")
    sh.add_argument("file")
    sh.add_argument("version", type=int)
    d = sub.add_parser("diff", help="сравнить две версии")
    d.add_argument("file")
    d.add_argument("a", type=int)
    d.add_argument("b", type=int)
    return p


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = VersionStore(args.file)
    try:
        if args.cmd == "save":
            e = store.save(args.message)
            print(f"Сохранена версия {e['id']} ({e['time']})")
        elif args.cmd == "list":
            for e in store.list_versions():
                print(f"v{e['id']:<3} {e['time']}  строк: {e['lines']:<4} {e['comment']}")
        elif args.cmd == "restore":
            e = store.restore(args.version)
            print(f"Версия {args.version} восстановлена, записана как v{e['id']}")
        elif args.cmd == "show":
            print(store.get_text(args.version), end="")
        else:
            return handle_extra(args, store)
    except VersionError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1
    return 0


def handle_extra(args, store) -> int:
    if args.cmd == "diff":
        for line in diff_lines(store.get_text(args.a), store.get_text(args.b)):
            print(line)
        return 0
    return 2


def main() -> None:
    sys.exit(run())

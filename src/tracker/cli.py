"""Консольный интерфейс change-tracker."""
from __future__ import annotations

import argparse
import sys

from .models import TrackerError
from .store import ChangeTracker


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="change-tracker")
    p.add_argument("--db", default="changes.json")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("--author", required=True)
    a.add_argument("--type", required=True)
    a.add_argument("--desc", required=True)
    s = sub.add_parser("status")
    s.add_argument("id")
    s.add_argument("status")
    link = sub.add_parser("link")
    link.add_argument("id")
    link.add_argument("commit")
    lst = sub.add_parser("list")
    lst.add_argument("--author")
    lst.add_argument("--type")
    lst.add_argument("--status")
    sub.add_parser("report").add_argument("out")
    return p


def run(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        tr = ChangeTracker(args.db)
        if args.cmd == "add":
            print("Создано", tr.add(args.author, args.type, args.desc).id)
        elif args.cmd == "status":
            c = tr.set_status(args.id, args.status)
            print(f"{c.id}: {c.status}")
        elif args.cmd == "link":
            c = tr.link_commit(args.id, args.commit)
            print(f"{c.id} ↔ {c.commit_hash}")
        elif args.cmd == "list":
            for c in tr.find(args.author, args.type, args.status):
                print(f"{c.id}  {c.date}  {c.author:<10} {c.type:<9} {c.status:<12} {c.commit_hash or '-'}  {c.description}")
        elif args.cmd == "report":
            from .report import export_json
            export_json(tr, args.out)
            print("Отчёт записан в", args.out)
    except TrackerError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1
    return 0


def main() -> None:
    sys.exit(run())

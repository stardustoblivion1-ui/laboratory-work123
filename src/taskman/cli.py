"""Консольный интерфейс team-tasks."""
from __future__ import annotations

import argparse
import sys

from .db import TaskDB, TaskError


def fmt(t: dict) -> str:
    return (f"#{t['id']:<3} [{t['status']:<11}] {t['priority']:<6} {t['due']}  "
            f"{t['assignee']:<10} {t['title']}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="team-tasks")
    p.add_argument("--db", default="tasks.db")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("title")
    a.add_argument("--assignee", required=True)
    a.add_argument("--priority", default="medium")
    a.add_argument("--due")
    sub.add_parser("list")
    u = sub.add_parser("update")
    u.add_argument("id", type=int)
    for f in ("title", "assignee", "priority", "status", "due"):
        u.add_argument(f"--{f}")
    sub.add_parser("delete").add_argument("id", type=int)
    # --- extra commands (сюда добавляют новые подкоманды) ---
    return p


def run(argv=None) -> int:
    args = build_parser().parse_args(argv)
    db = TaskDB(args.db)
    try:
        if args.cmd == "add":
            print("Создана задача", db.add(args.title, args.assignee, args.priority, args.due))
        elif args.cmd == "list":
            for t in db.all():
                print(fmt(t))
        elif args.cmd == "update":
            print(fmt(db.update(args.id, title=args.title, assignee=args.assignee,
                                priority=args.priority, status=args.status, due=args.due)))
        elif args.cmd == "delete":
            db.delete(args.id)
            print("Удалена задача", args.id)
        # --- extra dispatch (сюда добавляют обработчики новых подкоманд) ---
    except TaskError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()
    return 0


def main() -> None:
    sys.exit(run())

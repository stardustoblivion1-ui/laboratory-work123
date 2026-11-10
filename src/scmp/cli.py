"""Консольный интерфейс scmp."""
from __future__ import annotations

import argparse
import json
import sys

from . import baselines, changes, registry, releases
from .common import ScmError
from .db import connect


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="scmp")
    p.add_argument("--db", default="scmp.db")
    sub = p.add_subparsers(dest="group", required=True)

    pr = sub.add_parser("project").add_subparsers(dest="cmd", required=True)
    pr.add_parser("add").add_argument("name")
    pr.add_parser("list")

    ci = sub.add_parser("ci").add_subparsers(dest="cmd", required=True)
    c = ci.add_parser("add")
    c.add_argument("project")
    c.add_argument("name")
    c.add_argument("--version", default="1.0.0")
    ci.add_parser("list").add_argument("project")

    ch = sub.add_parser("change").add_subparsers(dest="cmd", required=True)
    c = ch.add_parser("create")
    c.add_argument("project")
    c.add_argument("title")
    c.add_argument("-d", "--description", default="")
    c = ch.add_parser("decide")
    c.add_argument("id", type=int)
    c.add_argument("decision", choices=["approve", "reject"])
    c.add_argument("--by", required=True)
    c.add_argument("--note", default="")
    c = ch.add_parser("apply")
    c.add_argument("id", type=int)
    c.add_argument("ci")
    c.add_argument("version")
    c.add_argument("--hash", default="")
    ch.add_parser("list").add_argument("project")

    bl = sub.add_parser("baseline").add_subparsers(dest="cmd", required=True)
    c = bl.add_parser("create")
    c.add_argument("project")
    c.add_argument("name")
    c = bl.add_parser("compare")
    c.add_argument("project")
    c.add_argument("a")
    c.add_argument("b")

    rl = sub.add_parser("release").add_subparsers(dest="cmd", required=True)
    c = rl.add_parser("register")
    c.add_argument("project")
    c.add_argument("version")
    c.add_argument("--baseline", required=True)

    sub.add_parser("report").add_argument("project")
    sub.add_parser("history").add_argument("project")
    return p


def _dispatch(conn, a) -> None:
    g, cmd = a.group, getattr(a, "cmd", None)
    if g == "project" and cmd == "add":
        print("Проект зарегистрирован, id =", registry.register_project(conn, a.name))
    elif g == "project":
        print("\n".join(registry.list_projects(conn)))
    elif g == "ci" and cmd == "add":
        registry.register_ci(conn, a.project, a.name, a.version)
        print(f"CI {a.project}/{a.name}@{a.version} зарегистрирована")
    elif g == "ci":
        for i in registry.list_cis(conn, a.project):
            print(f"{i['name']}@{i['version']}")
    elif g == "change" and cmd == "create":
        print("Создан запрос", changes.create_change(conn, a.project, a.title, a.description))
    elif g == "change" and cmd == "decide":
        print("Статус:", changes.decide(conn, a.id, a.decision == "approve", a.by, a.note))
    elif g == "change" and cmd == "apply":
        changes.apply_change(conn, a.id, a.ci, a.version, a.hash)
        print(f"Запрос {a.id} применён: {a.ci}@{a.version}")
    elif g == "change":
        for c in changes.list_changes(conn, a.project):
            print(f"#{c['id']} [{c['status']}] {c['title']}")
    elif g == "baseline" and cmd == "create":
        baselines.create_baseline(conn, a.project, a.name)
        print(f"Baseline {a.name} утверждена")
    elif g == "baseline":
        print(json.dumps(baselines.compare(conn, a.project, a.a, a.b), ensure_ascii=False, indent=2))
    elif g == "release":
        releases.register_release(conn, a.project, a.version, a.baseline)
        print(f"Релиз {a.version} зарегистрирован на {a.baseline}")
    elif g == "report":
        print(json.dumps(releases.report(conn, a.project), ensure_ascii=False, indent=2))
    elif g == "history":
        for h in releases.history(conn, a.project):
            print(f"{h['time']}  {h['action']:<16} {h['details']}")


def run(argv=None) -> int:
    a = build_parser().parse_args(argv)
    conn = connect(a.db)
    try:
        _dispatch(conn, a)
    except ScmError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()
    return 0


def main() -> None:
    sys.exit(run())

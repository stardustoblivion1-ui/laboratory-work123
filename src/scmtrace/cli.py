"""Консольный интерфейс scmtrace."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import baseline
from .audit import write_report
from .chain import build_chain, render
from .matrix import build_matrix, degree, render_markdown
from .registry import Registry, TraceError


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="scmtrace")
    p.add_argument("--db", default="scmtrace.db")
    p.add_argument("--root", default=".")
    s = p.add_subparsers(dest="cmd", required=True)
    c = s.add_parser("ci-add")
    c.add_argument("path")
    c.add_argument("--version", default="1.0.0")
    c = s.add_parser("request-create")
    c.add_argument("ci")
    c.add_argument("title")
    c.add_argument("version")
    c = s.add_parser("decide")
    c.add_argument("id")
    c.add_argument("decision", choices=["approve", "reject"])
    c.add_argument("--by", required=True)
    c.add_argument("--note", default="")
    s.add_parser("apply").add_argument("id")
    c = s.add_parser("link")
    c.add_argument("id")
    c.add_argument("--commit")
    c.add_argument("--test")
    c.add_argument("--baseline")
    c = s.add_parser("baseline")
    c.add_argument("--commit")
    s.add_parser("verify").add_argument("id")
    s.add_parser("audit").add_argument("--report", default="audit_report.json")
    s.add_parser("matrix").add_argument("--out")
    c = s.add_parser("chain")
    c.add_argument("id")
    c.add_argument("--report", default="audit_report.json")
    return p


def _dispatch(reg: Registry, a) -> int:
    if a.cmd == "ci-add":
        print("КЕ зарегистрирована:", reg.register_ci(a.root, a.path, a.version))
    elif a.cmd == "request-create":
        print("Создан запрос:", reg.create_request(a.ci, a.title, a.version))
    elif a.cmd == "decide":
        print("Статус:", reg.decide(a.id, a.decision == "approve", a.by, a.note))
    elif a.cmd == "apply":
        reg.apply(a.id, a.root)
        print("Запрос применён:", a.id)
    elif a.cmd == "link":
        print(reg.link(a.id, a.commit, a.test, a.baseline))
    elif a.cmd == "baseline":
        print("Baseline создана:", baseline.create_baseline(reg, a.root, a.commit))
    elif a.cmd == "verify":
        res = baseline.verify_baseline(reg, a.id, a.root)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res["ok"] else 1
    elif a.cmd == "audit":
        rep = write_report(reg, a.root, a.report)
        print(f"Аудит: {'соответствует' if rep['compliant'] else 'НЕСООТВЕТСТВИЯ: ' + str(len(rep['failed']))}; отчёт → {a.report}")
        return 0 if rep["compliant"] else 1
    elif a.cmd == "matrix":
        rows = build_matrix(a.root)
        text = render_markdown(rows)
        if a.out:
            Path(a.out).write_text(text, encoding="utf-8")
        print(text)
        print("Степень реализации:", json.dumps(degree(rows), ensure_ascii=False))
    elif a.cmd == "chain":
        print(render(build_chain(reg, a.root, a.id, a.report)))
    return 0


def run(argv=None) -> int:
    a = build_parser().parse_args(argv)
    reg = Registry(a.db)
    try:
        return _dispatch(reg, a)
    except TraceError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 2
    finally:
        reg.close()


def main() -> None:
    sys.exit(run())

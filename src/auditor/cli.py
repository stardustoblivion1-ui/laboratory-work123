"""Консольный интерфейс auditor."""
from __future__ import annotations

import argparse
import sys

from .audit import run_audit, write_html, write_json


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="auditor")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("audit")
    a.add_argument("project")
    a.add_argument("--rules", default="rules.json")
    a.add_argument("--json", default="report.json")
    a.add_argument("--html", default="report.html")
    return p


def run(argv=None) -> int:
    a = build_parser().parse_args(argv)
    report = run_audit(a.project, a.rules)
    write_json(report, a.json)
    write_html(report, a.html)
    s = report["summary"]
    print(f"{'СООТВЕТСТВУЕТ' if report['compliant'] else 'ЕСТЬ НАРУШЕНИЯ'}: "
          f"critical={s['critical']} high={s['high']} medium={s['medium']} low={s['low']}")
    return 0 if report["compliant"] else 1


def main() -> None:
    sys.exit(run())

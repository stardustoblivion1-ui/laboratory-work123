"""Консольный интерфейс cfgctl."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import baseline as bl
from .diff import compare, has_drift
from .report import write_report
from .scanner import ScanError, scan


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cfgctl")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("baseline")
    b.add_argument("root")
    b.add_argument("--by", required=True)
    b.add_argument("--dir", default="baselines")
    b.add_argument("--previous")
    b.add_argument("--exclude", nargs="*", default=[])
    c = sub.add_parser("check")
    c.add_argument("root")
    c.add_argument("--baseline", required=True)
    c.add_argument("--report", default="report.json")
    c.add_argument("--history", default="history.jsonl")
    c.add_argument("--exclude", nargs="*", default=[])
    return p


def run(argv=None) -> int:
    a = build_parser().parse_args(argv)
    try:
        if a.cmd == "baseline":
            data, path = bl.create(a.root, a.dir, a.by, a.previous, set(a.exclude))
            print(f"Создана {data['id']} → {path} ({len(data['items'])} единиц)")
            return 0
        base = bl.load(a.baseline)
        extra = [Path(a.baseline).parent, Path(a.report), Path(a.history)]
        current = scan(a.root, set(a.exclude), skip_paths=extra)
        drift = compare(base["items"], current)
        rep = write_report(base, drift, a.report, a.history)
        print(f"Baseline {base['id']}: добавлено {rep['summary']['added']}, "
              f"удалено {rep['summary']['removed']}, изменено {rep['summary']['modified']}")
        return 1 if has_drift(drift) else 0
    except (bl.BaselineError, ScanError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 2


def main() -> None:
    sys.exit(run())

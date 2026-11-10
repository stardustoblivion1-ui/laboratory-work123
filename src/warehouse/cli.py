"""Консольный интерфейс warehouse."""
from __future__ import annotations

import argparse
import sys

from .db import Warehouse, WarehouseError


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="warehouse")
    p.add_argument("--db", default="warehouse.db")
    sub = p.add_subparsers(dest="cmd", required=True)
    cat = sub.add_parser("category").add_subparsers(dest="sub", required=True)
    cat.add_parser("add").add_argument("name")
    prod = sub.add_parser("product").add_subparsers(dest="sub", required=True)
    pa = prod.add_parser("add")
    pa.add_argument("name")
    pa.add_argument("--category")
    pa.add_argument("--qty", type=int, default=0)
    prod.add_parser("delete").add_argument("name")
    for k in ("receive", "issue"):
        s = sub.add_parser(k)
        s.add_argument("name")
        s.add_argument("qty", type=int)
        s.add_argument("--note", default="")
    sub.add_parser("search").add_argument("text")
    sub.add_parser("report")
    sub.add_parser("journal")
    return p


def run(argv=None) -> int:
    a = build_parser().parse_args(argv)
    w = Warehouse(a.db)
    try:
        if a.cmd == "category":
            print("Категория создана, id =", w.add_category(a.name))
        elif a.cmd == "product" and a.sub == "add":
            print("Товар создан, id =", w.add_product(a.name, a.category, a.qty))
        elif a.cmd == "product":
            w.delete_product(a.name)
            print("Товар удалён")
        elif a.cmd == "receive":
            print("Остаток:", w.receive(a.name, a.qty, a.note))
        elif a.cmd == "issue":
            print("Остаток:", w.issue(a.name, a.qty, a.note))
        elif a.cmd == "search":
            for r in w.search(a.text):
                print(f"{r['name']} ({r['category'] or '—'}): {r['quantity']}")
        elif a.cmd == "report":
            for r in w.stock_report():
                print(f"{r['category']:<14}{r['name']:<20}{r['quantity']:>6}")
        elif a.cmd == "journal":
            for r in w.journal():
                print(f"{r['id']:>3} {r['time']} {r['kind']:<7} {r['product']} x{r['quantity']} {r['note']}")
    except WarehouseError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1
    finally:
        w.close()
    return 0


def main() -> None:
    sys.exit(run())

"""Сравнение baseline с текущим состоянием."""
from __future__ import annotations


def compare(baseline_items: dict, current_items: dict) -> dict:
    b, c = set(baseline_items), set(current_items)
    return {
        "added": sorted(c - b),
        "removed": sorted(b - c),
        "modified": sorted(p for p in b & c
                           if baseline_items[p]["sha256"] != current_items[p]["sha256"]),
    }


def has_drift(d: dict) -> bool:
    return any(d[k] for k in ("added", "removed", "modified"))

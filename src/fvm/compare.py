"""Построчное сравнение версий (+ добавлено, - удалено)."""
from __future__ import annotations

import difflib


def diff_lines(old: str, new: str) -> list[str]:
    out: list[str] = []
    for line in difflib.ndiff(old.splitlines(), new.splitlines()):
        if line.startswith("+ "):
            out.append("+ " + line[2:])
        elif line.startswith("- "):
            out.append("- " + line[2:])
        elif line.startswith("  "):
            out.append("  " + line[2:])
    return out


def has_changes(diff: list[str]) -> bool:
    return any(d[0] in "+-" for d in diff)

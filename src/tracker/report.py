"""Экспорт отчёта JSON: все изменения + сводка по статусам и трассировка к коммитам."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .store import ChangeTracker


def build_report(tr: ChangeTracker) -> dict:
    items = [c.to_dict() for c in tr.changes.values()]
    return {
        "total": len(items),
        "by_status": dict(Counter(c["status"] for c in items)),
        "traceable": [{"id": c["id"], "commit_hash": c["commit_hash"]}
                      for c in items if c["commit_hash"]],
        "without_commit": [c["id"] for c in items if not c["commit_hash"]],
        "changes": items,
    }


def export_json(tr: ChangeTracker, out: str | Path) -> Path:
    out = Path(out)
    out.write_text(json.dumps(build_report(tr), ensure_ascii=False, indent=2), encoding="utf-8")
    return out

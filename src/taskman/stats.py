"""Статистика выполнения задач."""
from __future__ import annotations

from collections import Counter

from .db import TaskDB


def statistics(db: TaskDB) -> dict:
    tasks = db.all()
    total = len(tasks)
    done = sum(t["status"] == "done" for t in tasks)
    return {
        "total": total,
        "done": done,
        "percent_done": round(100 * done / total, 1) if total else 0.0,
        "by_status": dict(Counter(t["status"] for t in tasks)),
        "by_assignee": dict(Counter(t["assignee"] for t in tasks)),
    }

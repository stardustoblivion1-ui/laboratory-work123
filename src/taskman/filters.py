"""Фильтрация задач по исполнителю, приоритету и статусу."""
from __future__ import annotations

from .db import TaskDB


def filter_tasks(db: TaskDB, assignee=None, priority=None, status=None) -> list[dict]:
    return [t for t in db.all()
            if (assignee is None or t["assignee"] == assignee)
            and (priority is None or t["priority"] == priority)
            and (status is None or t["status"] == status)]

"""Хранилище задач в SQLite."""
from __future__ import annotations

import sqlite3
from datetime import date

PRIORITIES = ("low", "medium", "high")
STATUSES = ("todo", "in_progress", "done")


class TaskError(Exception):
    """Ошибка работы с задачами."""


def validate(title=None, assignee=None, priority=None, status=None, due=None) -> None:
    if title is not None and not title.strip():
        raise TaskError("Название задачи не может быть пустым")
    if assignee is not None and not assignee.strip():
        raise TaskError("Исполнитель не может быть пустым")
    if priority is not None and priority not in PRIORITIES:
        raise TaskError(f"Приоритет должен быть одним из: {', '.join(PRIORITIES)}")
    if status is not None and status not in STATUSES:
        raise TaskError(f"Статус должен быть одним из: {', '.join(STATUSES)}")
    if due is not None:
        try:
            date.fromisoformat(due)
        except ValueError:
            raise TaskError("Дата должна быть в формате ГГГГ-ММ-ДД") from None


class TaskDB:
    def __init__(self, path: str = "tasks.db"):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                assignee TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'todo',
                due TEXT NOT NULL)"""
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def add(self, title: str, assignee: str, priority: str = "medium", due: str | None = None) -> int:
        due = due or date.today().isoformat()
        validate(title, assignee, priority, None, due)
        cur = self.conn.execute(
            "INSERT INTO tasks (title, assignee, priority, due) VALUES (?,?,?,?)",
            (title.strip(), assignee.strip(), priority, due))
        self.conn.commit()
        return cur.lastrowid

    def get(self, task_id: int) -> dict:
        row = self.conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row is None:
            raise TaskError(f"Задача {task_id} не найдена")
        return dict(row)

    def all(self) -> list[dict]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM tasks ORDER BY id")]

    def update(self, task_id: int, **fields) -> dict:
        fields = {k: v for k, v in fields.items() if v is not None}
        unknown = set(fields) - {"title", "assignee", "priority", "status", "due"}
        if unknown:
            raise TaskError(f"Неизвестные поля: {', '.join(sorted(unknown))}")
        self.get(task_id)
        validate(**fields)
        if fields:
            sets = ", ".join(f"{k}=?" for k in fields)
            self.conn.execute(f"UPDATE tasks SET {sets} WHERE id=?", (*fields.values(), task_id))
            self.conn.commit()
        return self.get(task_id)

    def delete(self, task_id: int) -> None:
        self.get(task_id)
        self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.conn.commit()

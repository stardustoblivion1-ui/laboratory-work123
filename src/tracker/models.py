"""Модель запроса на изменение и правила статусов."""
from __future__ import annotations

from dataclasses import asdict, dataclass

STATUSES = ("planned", "in_progress", "done")  # запланировано, в работе, завершено
TYPES = ("feature", "bugfix", "refactor", "docs")
TRANSITIONS = {"planned": {"in_progress"}, "in_progress": {"done"}, "done": set()}


class TrackerError(Exception):
    """Ошибка журнала изменений."""


@dataclass
class Change:
    id: str
    author: str
    date: str
    type: str
    description: str
    status: str = "planned"
    commit_hash: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

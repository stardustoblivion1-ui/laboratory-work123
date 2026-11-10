"""Журнал с постоянным хранением в JSON."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .models import STATUSES, TRANSITIONS, TYPES, Change, TrackerError


class ChangeTracker:
    def __init__(self, path: str | Path = "changes.json"):
        self.path = Path(path)
        self.changes: dict[str, Change] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.changes = {r["id"]: Change(**r) for r in raw}
        except (json.JSONDecodeError, TypeError, KeyError) as exc:
            raise TrackerError(f"Повреждён файл журнала: {exc}") from exc

    def _save(self) -> None:
        data = [c.to_dict() for c in self.changes.values()]
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _next_id(self) -> str:
        return f"CH-{len(self.changes) + 1:03d}"

    def add(self, author: str, type_: str, description: str,
            change_id: str | None = None, when: str | None = None) -> Change:
        if not author.strip() or not description.strip():
            raise TrackerError("Автор и описание обязательны")
        if type_ not in TYPES:
            raise TrackerError(f"Неизвестный тип {type_!r}; допустимо: {', '.join(TYPES)}")
        cid = change_id or self._next_id()
        if cid in self.changes:
            raise TrackerError(f"ID {cid} уже существует")
        ch = Change(cid, author.strip(), when or date.today().isoformat(), type_, description.strip())
        self.changes[cid] = ch
        self._save()
        return ch

    def get(self, change_id: str) -> Change:
        try:
            return self.changes[change_id]
        except KeyError:
            raise TrackerError(f"Изменение {change_id} не найдено") from None

    def set_status(self, change_id: str, status: str) -> Change:
        if status not in STATUSES:
            raise TrackerError(f"Некорректный статус {status!r}; допустимо: {', '.join(STATUSES)}")
        ch = self.get(change_id)
        if status not in TRANSITIONS[ch.status]:
            raise TrackerError(f"Переход {ch.status} → {status} недопустим")
        ch.status = status
        self._save()
        return ch

    def link_commit(self, change_id: str, commit_hash: str) -> Change:
        h = commit_hash.strip().lower()
        if not (7 <= len(h) <= 40) or any(c not in "0123456789abcdef" for c in h):
            raise TrackerError("commit_hash должен быть hex-строкой длиной 7–40 символов")
        ch = self.get(change_id)
        ch.commit_hash = h
        self._save()
        return ch

    def find(self, author: str | None = None, type_: str | None = None,
             status: str | None = None) -> list[Change]:
        return [
            c for c in self.changes.values()
            if (author is None or c.author == author)
            and (type_ is None or c.type == type_)
            and (status is None or c.status == status)
        ]

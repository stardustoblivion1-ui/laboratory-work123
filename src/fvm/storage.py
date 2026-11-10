"""Хранилище версий: каждая версия — отдельный файл + запись в index.json."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

STORE_DIR = ".fvm"


class VersionError(Exception):
    """Ошибка работы с версиями (нет версии, нет файла, неверный ввод)."""


class VersionStore:
    def __init__(self, document: str | Path, root: str | Path | None = None):
        self.document = Path(document)
        if not self.document.name:
            raise VersionError("Не указано имя документа")
        base = Path(root) if root else self.document.parent
        self.dir = base / STORE_DIR / self.document.name
        self.index_file = self.dir / "index.json"

    def _load(self) -> list[dict]:
        if not self.index_file.exists():
            return []
        try:
            return json.loads(self.index_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise VersionError(f"Повреждён индекс версий: {exc}") from exc

    def _write(self, index: list[dict]) -> None:
        self.index_file.write_text(
            json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def save(self, comment: str = "") -> dict:
        """Сохраняет текущее содержимое документа как новую версию."""
        if not self.document.is_file():
            raise VersionError(f"Файл не найден: {self.document}")
        return self.save_text(self.document.read_text(encoding="utf-8"), comment)

    def save_text(self, text: str, comment: str = "") -> dict:
        self.dir.mkdir(parents=True, exist_ok=True)
        index = self._load()
        vid = index[-1]["id"] + 1 if index else 1
        (self.dir / f"v{vid:04d}.txt").write_text(text, encoding="utf-8")
        entry = {
            "id": vid,
            "time": datetime.now().isoformat(timespec="seconds"),
            "comment": comment,
            "lines": len(text.splitlines()),
        }
        index.append(entry)
        self._write(index)
        return entry

    def list_versions(self) -> list[dict]:
        return self._load()

    def get_text(self, version: int) -> str:
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise VersionError(f"Некорректный номер версии: {version!r}")
        if version not in {e["id"] for e in self._load()}:
            raise VersionError(f"Версия {version} не найдена")
        return (self.dir / f"v{version:04d}.txt").read_text(encoding="utf-8")

    def restore(self, version: int) -> dict:
        """Восстанавливает версию в рабочий файл; история не удаляется —
        восстановленное состояние записывается как новая версия."""
        text = self.get_text(version)
        self.document.write_text(text, encoding="utf-8")
        return self.save_text(text, comment=f"restore of v{version}")

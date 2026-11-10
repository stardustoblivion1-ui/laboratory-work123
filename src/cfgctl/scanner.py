"""Рекурсивное сканирование каталога: относительные пути, размер, SHA-256."""
from __future__ import annotations

import hashlib
from pathlib import Path

DEFAULT_EXCLUDES = {".git", "__pycache__", "venv", ".venv", ".pytest_cache", ".ruff_cache"}


class ScanError(Exception):
    """Ошибка сканирования."""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def scan(root: str | Path, exclude: set[str] | None = None,
         skip_paths: list[Path] | None = None) -> dict[str, dict]:
    """Возвращает {относительный_путь: {size, sha256}}.

    exclude    — имена каталогов/файлов (любой уровень вложенности);
    skip_paths — конкретные файлы/каталоги (например, сам файл снимка), которые
                 не должны попадать в результат.
    """
    root = Path(root).resolve()
    if not root.is_dir():
        raise ScanError(f"Каталог не найден: {root}")
    names = DEFAULT_EXCLUDES | set(exclude or ())
    skips = [Path(p).resolve() for p in (skip_paths or [])]
    result: dict[str, dict] = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in names for part in rel.parts):
            continue
        resolved = path.resolve()
        if any(resolved == s or s in resolved.parents for s in skips):
            continue
        if path.is_file():
            result[rel.as_posix()] = {"size": path.stat().st_size, "sha256": sha256_file(path)}
    return result

"""Baseline — утверждённый неизменяемый снимок конфигурационных единиц."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

from .scanner import scan


class BaselineError(Exception):
    """Ошибка работы с baseline."""


def _seal(data: dict) -> str:
    body = {k: v for k, v in data.items() if k != "seal"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def git_commit(root: Path) -> str | None:
    try:
        out = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                             capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def next_id(directory: Path) -> str:
    nums = [int(p.stem.split("-")[1]) for p in directory.glob("BL-*.json")
            if p.stem.split("-")[1].isdigit()]
    return f"BL-{max(nums, default=0) + 1:04d}"


def create(root: str | Path, directory: str | Path, approved_by: str,
           previous_id: str | None = None, exclude: set[str] | None = None,
           commit_hash: str | None = None) -> tuple[dict, Path]:
    """Создаёт НОВУЮ baseline. Существующие файлы не перезаписываются."""
    if not approved_by.strip():
        raise BaselineError("Не указано утверждающее лицо")
    root, directory = Path(root), Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if previous_id and not (directory / f"{previous_id}.json").exists():
        raise BaselineError(f"Предыдущая baseline {previous_id} не найдена")
    bid = next_id(directory)
    path = directory / f"{bid}.json"
    if path.exists():
        raise BaselineError(f"{bid} уже утверждена и не может быть изменена")
    data = {
        "id": bid,
        "date": datetime.now().isoformat(timespec="seconds"),
        "approved_by": approved_by.strip(),
        "commit_hash": commit_hash or git_commit(root),
        "previous": previous_id,
        "items": scan(root, exclude, skip_paths=[directory]),
    }
    data["seal"] = _seal(data)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.chmod(path, 0o444)  # утверждённая baseline — только для чтения
    return data, path


def load(path: str | Path) -> dict:
    path = Path(path)
    if not path.is_file():
        raise BaselineError(f"Baseline не найдена: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BaselineError(f"Baseline повреждена: {exc}") from exc
    if data.get("seal") != _seal(data):
        raise BaselineError("Нарушена целостность baseline (контрольная сумма не совпадает)")
    return data

"""Загрузка правил из JSON (устойчиво к отсутствию и повреждению файла)."""
from __future__ import annotations

import json
from pathlib import Path

DEFAULT_RULES = {
    "required_files": [
        {"path": "README.md", "severity": "high"},
        {"path": "CHANGELOG.md", "severity": "medium"},
        {"path": "pyproject.toml", "severity": "high"},
    ],
    "git": {"severity": "critical"},
    "ci": {"severity": "medium", "dir": ".github/workflows"},
    "version": {"file": "pyproject.toml", "severity": "high"},
    "min_commits": {"count": 3, "severity": "medium"},
}
SEVERITIES = ("critical", "high", "medium", "low")


def load_rules(path: str | Path | None) -> tuple[dict, list[str]]:
    """Возвращает (правила, предупреждения). При проблеме — правила по умолчанию."""
    if path is None:
        return DEFAULT_RULES, []
    p = Path(path)
    if not p.is_file():
        return DEFAULT_RULES, [f"Файл правил {p} не найден — применены правила по умолчанию"]
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise TypeError("корень должен быть объектом")
    except (json.JSONDecodeError, TypeError, ValueError, UnicodeDecodeError, OSError) as exc:
        return DEFAULT_RULES, [f"Файл правил {p} повреждён ({exc}) — применены правила по умолчанию"]
    return data, []


def severity_of(cfg: dict, default: str = "medium") -> str:
    s = cfg.get("severity", default) if isinstance(cfg, dict) else default
    return s if s in SEVERITIES else default

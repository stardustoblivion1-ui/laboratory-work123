"""Общие утилиты: ошибки, SemVer, время, журнал."""
from __future__ import annotations

import re
from datetime import datetime

SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


class ScmError(Exception):
    """Ошибка платформы управления конфигурацией."""


def parse_semver(v: str) -> tuple[int, int, int]:
    m = SEMVER.match(v) if isinstance(v, str) else None
    if not m:
        raise ScmError(f"Некорректная версия {v!r}: ожидается MAJOR.MINOR.PATCH")
    return tuple(int(x) for x in m.groups())


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def log(conn, project_id: int | None, action: str, details: str = "") -> None:
    conn.execute("INSERT INTO history (time, project_id, action, details) VALUES (?,?,?,?)",
                 (now(), project_id, action, details))


def require_text(value: str, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ScmError(f"{what} не может быть пустым")
    return value.strip()

"""SemVer: разбор, сравнение, повышение, чтение/запись версии в pyproject.toml."""
from __future__ import annotations

import re
from pathlib import Path

SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
TAG = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
_VERSION_LINE = re.compile(r'^(version\s*=\s*)"([^"]*)"', re.MULTILINE)


class VersionError(Exception):
    """Ошибка версии или релизного процесса."""


def parse(version: str) -> tuple[int, int, int]:
    m = SEMVER.match(version.strip()) if isinstance(version, str) else None
    if not m:
        raise VersionError(
            f"Некорректная версия {version!r}: ожидается формат MAJOR.MINOR.PATCH (например, 1.2.3)")
    return tuple(int(x) for x in m.groups())


def bump(version: str, part: str) -> str:
    major, minor, patch = parse(version)
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise VersionError(f"Неизвестная часть версии {part!r}: допустимо major, minor, patch")


def read_version(pyproject: str | Path) -> str:
    path = Path(pyproject)
    if not path.is_file():
        raise VersionError(f"Файл не найден: {path}")
    m = _VERSION_LINE.search(path.read_text(encoding="utf-8"))
    if not m:
        raise VersionError(f"В {path} не найдено поле version")
    parse(m.group(2))
    return m.group(2)


def write_version(pyproject: str | Path, new: str) -> None:
    parse(new)
    path = Path(pyproject)
    text = path.read_text(encoding="utf-8")
    if not _VERSION_LINE.search(text):
        raise VersionError(f"В {path} не найдено поле version")
    path.write_text(_VERSION_LINE.sub(lambda m: f'{m.group(1)}"{new}"', text, count=1),
                    encoding="utf-8")

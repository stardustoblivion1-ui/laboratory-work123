"""Регистрация релиза и проверка Git-тега (только для релизной сборки)."""
from __future__ import annotations

from pathlib import Path

from .changelog import add_release, released_versions
from .version import TAG, VersionError, bump, parse, read_version, write_version


def register(pyproject: str | Path, changelog: str | Path, new_version: str,
             changes: list[str]) -> str:
    """Записывает новую версию в pyproject и CHANGELOG.
    Запрещены повтор существующей версии и уменьшение номера."""
    current = read_version(pyproject)
    if new_version in released_versions(changelog) or new_version == current:
        raise VersionError(f"Версия {new_version} уже существует")
    if parse(new_version) < parse(current):
        raise VersionError(f"Нельзя уменьшать версию: {current} → {new_version}")
    add_release(changelog, new_version, changes)
    write_version(pyproject, new_version)
    return new_version


def register_bump(pyproject: str | Path, changelog: str | Path, part: str,
                  changes: list[str]) -> str:
    return register(pyproject, changelog, bump(read_version(pyproject), part), changes)


def check_tag(tag: str | None, pyproject: str | Path) -> str:
    """Проверка соответствия тега vX.Y.Z версии пакета. Вызывается ТОЛЬКО релизным workflow."""
    if not tag:
        raise VersionError("Git-тег не указан (ожидается тег вида vX.Y.Z)")
    if not TAG.match(tag):
        raise VersionError(f"Некорректный формат тега {tag!r}: ожидается vX.Y.Z (например, v1.0.0)")
    version = read_version(pyproject)
    if tag[1:] != version:
        raise VersionError(
            f"Тег {tag} не соответствует версии пакета {version} в pyproject.toml")
    return version

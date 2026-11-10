"""История релизов в CHANGELOG.md."""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from .version import VersionError, parse

_ENTRY = re.compile(r"^## \[(\d+\.\d+\.\d+)\]", re.MULTILINE)


def released_versions(changelog: str | Path) -> list[str]:
    path = Path(changelog)
    if not path.is_file():
        return []
    return _ENTRY.findall(path.read_text(encoding="utf-8"))


def add_release(changelog: str | Path, version: str, changes: list[str],
                when: str | None = None) -> None:
    parse(version)
    if not changes:
        raise VersionError("Укажите хотя бы одно изменение для записи в CHANGELOG")
    path = Path(changelog)
    if version in released_versions(path):
        raise VersionError(f"Версия {version} уже зарегистрирована в {path.name}")
    entry = f"## [{version}] - {when or date.today().isoformat()}\n" + "".join(
        f"- {c}\n" for c in changes)
    text = path.read_text(encoding="utf-8") if path.is_file() else "# Changelog\n"
    head, sep, rest = text.partition("\n## ")
    new = head.rstrip("\n") + "\n\n" + entry + ("\n## " + rest if sep else "")
    path.write_text(new, encoding="utf-8")

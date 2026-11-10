"""Проверки соблюдения правил. Каждая возвращает список результатов и не бросает исключений."""
from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

from .rules import severity_of

SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def result(rule: str, category: str, severity: str, passed: bool, message: str) -> dict:
    return {"rule": rule, "category": category, "severity": severity,
            "passed": passed, "message": message}


def check_files(root: Path, rules: dict) -> list[dict]:
    out = []
    for item in rules.get("required_files", []):
        if not isinstance(item, dict) or "path" not in item:
            out.append(result("required_files", "files", "medium", False,
                              f"Некорректное описание правила файла: {item!r}"))
            continue
        ok = (root / item["path"]).is_file()
        out.append(result(f"file:{item['path']}", "files", severity_of(item), ok,
                          f"{item['path']} найден" if ok else f"Отсутствует файл {item['path']}"))
    return out


def _git(root: Path, *args: str) -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                           text=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def check_git(root: Path, rules: dict) -> list[dict]:
    cfg = rules.get("git")
    if cfg is None:
        return []
    ok = (root / ".git").exists() and _git(root, "rev-parse", "--git-dir") is not None
    return [result("git", "git", severity_of(cfg, "critical"), ok,
                   "Git-репозиторий найден" if ok else "Каталог не является Git-репозиторием")]


def check_commits(root: Path, rules: dict) -> list[dict]:
    cfg = rules.get("min_commits")
    if cfg is None:
        return []
    need = cfg.get("count", 1) if isinstance(cfg, dict) else 1
    out = _git(root, "rev-list", "--count", "HEAD")
    sev = severity_of(cfg)
    if out is None or not out.isdigit():
        return [result("min_commits", "git", sev, False,
                       "Невозможно подсчитать коммиты (нет репозитория или коммитов)")]
    n = int(out)
    return [result("min_commits", "git", sev, n >= need, f"Коммитов: {n}, требуется не менее {need}")]


def check_ci(root: Path, rules: dict) -> list[dict]:
    cfg = rules.get("ci")
    if cfg is None:
        return []
    d = root / cfg.get("dir", ".github/workflows")
    files = [*d.glob("*.yml"), *d.glob("*.yaml")] if d.is_dir() else []
    return [result("ci", "ci", severity_of(cfg), bool(files),
                   f"CI workflow найден: {files[0].name}" if files
                   else f"В {d.relative_to(root)} нет workflow-файлов (*.yml)")]


def check_version(root: Path, rules: dict) -> list[dict]:
    cfg = rules.get("version")
    if cfg is None:
        return []
    sev = severity_of(cfg, "high")
    path = root / cfg.get("file", "pyproject.toml")
    if not path.is_file():
        return [result("version", "version", sev, False, f"Нет файла {path.name} для чтения версии")]
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        return [result("version", "version", sev, False, f"Файл {path.name} повреждён: {exc}")]
    version = data.get("project", {}).get("version")
    if not isinstance(version, str):
        return [result("version", "version", sev, False, "В [project] не задано поле version")]
    ok = bool(SEMVER.match(version))
    return [result("version", "version", sev, ok,
                   f"Версия {version} соответствует MAJOR.MINOR.PATCH" if ok
                   else f"Версия {version!r} не соответствует формату MAJOR.MINOR.PATCH")]


ALL_CHECKS = (check_files, check_git, check_commits, check_ci, check_version)

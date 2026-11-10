# Отчёт по практической работе №19–20 — задание 6

**Тема:** Автоматизация программных релизов  
**Репозиторий:** `release-manager` (локальный Git-репозиторий; ссылка на GitHub — _вставить_)

## 1. Цель работы
Создать менеджер SemVer-версий и автоматизированную сборку пакета по Git-тегу с проверкой соответствия версии.

## 2. Схема алгоритма
```
bump part: разобрать версию → увеличить часть, обнулить младшие → проверить уникальность и отсутствие уменьшения → запись в CHANGELOG и pyproject
check-tag tag: тег указан? → формат vX.Y.Z? → tag[1:] == версия pyproject? иначе exit 1
release.yml (тег v*): check-tag → pytest → python -m build → upload-artifact
```

## 3. Описание архитектуры
`version.py` (SemVer, pyproject), `changelog.py`, `release.py` (register, check_tag), `cli.py`; workflows `ci.yml` (push/PR, только тесты) и `release.yml` (только теги v*).

## 4. Основные фрагменты кода
**`src/relman/version.py` — `bump`**
```python
def bump(version: str, part: str) -> str:
    major, minor, patch = parse(version)
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise VersionError(f"Неизвестная часть версии {part!r}: допустимо major, minor, patch")
```

**`src/relman/release.py` — `register`**
```python
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
```

**`src/relman/release.py` — `check_tag`**
```python
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
```

## 5. Результаты запуска
### Тесты (pytest)
```
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-9.2.0, pluggy-1.7.0 -- /Users/wincerdion/Documents/123/scm_practice/.venv/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/wincerdion/Documents/123/scm_practice/release-manager
configfile: pyproject.toml
testpaths: tests
collecting ... collected 17 items

tests/test_version.py::test_invalid_semver[1.2] PASSED                   [  5%]
tests/test_version.py::test_invalid_semver[1.2.3.4] PASSED               [ 11%]
tests/test_version.py::test_invalid_semver[v1.2.3] PASSED                [ 17%]
tests/test_version.py::test_invalid_semver[01.2.3] PASSED                [ 23%]
tests/test_version.py::test_invalid_semver[a.b.c] PASSED                 [ 29%]
tests/test_version.py::test_invalid_semver[] PASSED                      [ 35%]
tests/test_version.py::test_invalid_semver[1.2.x] PASSED                 [ 41%]
tests/test_version.py::test_bump_resets_lower_parts PASSED               [ 47%]
tests/test_version.py::test_read_write_version PASSED                    [ 52%]
tests/test_version.py::test_register_updates_pyproject_and_changelog PASSED [ 58%]
tests/test_version.py::test_duplicate_version_rejected PASSED            [ 64%]
tests/test_version.py::test_decrease_rejected PASSED                     [ 70%]
tests/test_version.py::test_tag_matches_version PASSED                   [ 76%]
tests/test_version.py::test_tag_mismatch_missing_and_bad_format PASSED   [ 82%]
tests/test_version.py::test_missing_files PASSED                         [ 88%]
tests/test_version.py::test_cli_bump_and_check_tag PASSED                [ 94%]
tests/test_version.py::test_empty_changes_rejected PASSED                [100%]

============================== 17 passed in 0.03s ==============================
```
### Статический анализ (ruff)
```
All checks passed!
```
### Git: ветки, коммиты, теги
Ветки: main; коммитов: 5; теги: v1.0.0
```
* 94bf426 (HEAD -> main) docs: CI evidence template for release scenarios
* dce1ef2 (tag: v1.0.0) release: 1.0.0
* 35f245e ci: tests workflow and tag-triggered release workflow; docs
* 2ec5ea8 feat: SemVer parsing/bump, changelog history, release registration and tag check
* 4d3553d chore: init project, pyproject (0.9.0), CHANGELOG
```

## Подтверждение CI
Workflow-файлы лежат в `.github/workflows/`. Ссылки/скриншоты запусков GitHub Actions обязательны для заданий 5–9 — вставьте их после `git push` в раздел ниже (шаблон — `docs/CI_EVIDENCE.md` там, где он есть):
- Ссылка на репозиторий: _вставить_
- Ссылки на запуски Actions: _вставить_

## 6. Связь с конфигурационным управлением
Управление выпуском: единый источник версии, история релизов, проверка соответствия тега версии до создания артефактов, воспроизводимая сборка. Инструкция установки — INSTALL.md.

## 7. Ограничения системы
Публикация (PyPI) и развёртывание не выполняются; запуски Actions и скриншоты нужно добавить после push (`docs/CI_EVIDENCE.md`); локально проверены те же команды check-tag и сборка wheel/sdist.

## 8. Вывод
В ходе работы выполнено задание 6: «Автоматизация программных релизов». Функциональные требования реализованы, автоматические тесты проходят, изменения оформлены в Git (ветки, содержательные коммиты, тег). Результаты подтверждают работоспособность решения в пределах перечисленных ограничений.

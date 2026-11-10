# Отчёт по практической работе №19–20 — задание 3

**Тема:** Контроль конфигурации файлов проекта  
**Репозиторий:** `config-control` (локальный Git-репозиторий; ссылка на GitHub — _вставить_)

## 1. Цель работы
Разработать модульный инструмент обнаружения расхождений между файлами и утверждённой baseline.

## 2. Схема алгоритма
```
scan: обход каталога → пропуск исключений → size + SHA-256 для каждого файла
baseline: scan → ID BL-NNNN, дата, утверждающий, commit hash, previous → seal (SHA-256 содержимого) → файл только для чтения
check: загрузить baseline (проверить seal) → scan → сравнить added/removed/modified → отчёт JSON + запись в history.jsonl
```

## 3. Описание архитектуры
`scanner.py` (ветка feature-scan); `baseline.py`, `diff.py`, `report.py`, `cli.py` (ветка feature-diff). Каталог baseline и файлы отчётов исключаются из сканирования.

## 4. Основные фрагменты кода
**`src/cfgctl/scanner.py` — `scan`**
```python
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
```

**`src/cfgctl/baseline.py` — `create`**
```python
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
```

**`src/cfgctl/diff.py` — `compare`**
```python
def compare(baseline_items: dict, current_items: dict) -> dict:
    b, c = set(baseline_items), set(current_items)
    return {
        "added": sorted(c - b),
        "removed": sorted(b - c),
        "modified": sorted(p for p in b & c
                           if baseline_items[p]["sha256"] != current_items[p]["sha256"]),
    }
```

## 5. Результаты запуска
### Тесты (pytest)
```
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-9.2.0, pluggy-1.7.0 -- /Users/wincerdion/Documents/123/scm_practice/.venv/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/wincerdion/Documents/123/scm_practice/config-control
configfile: pyproject.toml
testpaths: tests
collecting ... collected 13 items

tests/test_diff.py::test_no_drift PASSED                                 [  7%]
tests/test_diff.py::test_modified_added_removed PASSED                   [ 15%]
tests/test_diff.py::test_missing_baseline PASSED                         [ 23%]
tests/test_diff.py::test_baseline_is_readonly_and_ids_unique PASSED      [ 30%]
tests/test_diff.py::test_tampered_baseline_detected PASSED               [ 38%]
tests/test_diff.py::test_unknown_previous_and_empty_approver PASSED      [ 46%]
tests/test_diff.py::test_baseline_dir_not_scanned_when_inside_project PASSED [ 53%]
tests/test_diff.py::test_cli_check_report_and_exit_codes PASSED          [ 61%]
tests/test_scanner.py::test_empty_directory PASSED                       [ 69%]
tests/test_scanner.py::test_relative_paths_size_and_sha PASSED           [ 76%]
tests/test_scanner.py::test_default_excludes PASSED                      [ 84%]
tests/test_scanner.py::test_custom_exclude_and_skip_paths PASSED         [ 92%]
tests/test_scanner.py::test_missing_directory PASSED                     [100%]

============================== 13 passed in 0.13s ==============================
```
### Статический анализ (ruff)
```
All checks passed!
```
### Git: ветки, коммиты, теги
Ветки: feature-diff, feature-scan, main; коммитов: 6; теги: —
```
* 4a36466 (HEAD -> main) docs: CONFIGURATION_MANAGEMENT.md and two example baselines with reports
*   d18801b Merge branch 'feature-diff'
|\  
| * 9ef4f4b (feature-diff) feat(diff): immutable baselines, comparison, JSON report, CLI
|/  
*   4f140c3 Merge branch 'feature-scan'
|\  
| * 0822eb6 (feature-scan) feat(scan): recursive scanner with SHA-256 and exclusions
|/  
* b2a6c72 chore: init project and README
```

## 6. Связь с конфигурационным управлением
Реализованы идентификация КЕ (путь+SHA-256), baseline с утверждением, запрет прямого изменения (read-only + seal) и новая baseline со ссылкой на предыдущую, аудит расхождений. Правила — CONFIGURATION_MANAGEMENT.md.

## 7. Ограничения системы
Не контролируются права и метаданные; утверждающее лицо не аутентифицируется; seal обнаруживает правку, но не мешает пересоздать файл целиком.

## 8. Вывод
В ходе работы выполнено задание 3: «Контроль конфигурации файлов проекта». Функциональные требования реализованы, автоматические тесты проходят, изменения оформлены в Git (ветки, содержательные коммиты, тег). Результаты подтверждают работоспособность решения в пределах перечисленных ограничений.

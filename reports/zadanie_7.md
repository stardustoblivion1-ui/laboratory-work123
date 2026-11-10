# Отчёт по практической работе №19–20 — задание 7

**Тема:** Аудит конфигурации программного проекта  
**Репозиторий:** `config-auditor` (локальный Git-репозиторий; ссылка на GitHub — _вставить_)

## 1. Цель работы
Создать конфигурируемый аудитор правил проекта с отчётами JSON и HTML.

## 2. Схема алгоритма
```
load_rules (при ошибке — правила по умолчанию + предупреждение) → для каждой проверки (файлы, git, коммиты, CI, версия) собрать результат {rule, category, severity, passed, message} → итоговый отчёт → JSON и HTML; exit 0/1
```

## 3. Описание архитектуры
`rules.py` (загрузка правил), `checks.py` (проверки), `audit.py` (запуск и отчёты), `cli.py`; правила — `rules.json`; workflow `audit.yml` запускает тесты и самоаудит.

## 4. Основные фрагменты кода
**`src/auditor/checks.py` — `check_version`**
```python
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
```

**`src/auditor/audit.py` — `run_audit`**
```python
def run_audit(project: str | Path, rules_path: str | Path | None = None) -> dict:
    root = Path(project)
    rules, warnings = load_rules(rules_path)
    results: list[dict] = []
    if not root.is_dir():
        results.append(result("project", "files", "critical", False, f"Каталог проекта не найден: {root}"))
    else:
        for check in ALL_CHECKS:
            try:
                results.extend(check(root, rules))
            except Exception as exc:  # noqa: BLE001 - аудитор не должен аварийно завершаться
                results.append(result(check.__name__, "internal", "high", False,
                                      f"Ошибка выполнения проверки: {exc}"))
    for w in warnings:
        results.append(result("rules", "config", "high", False, w))
    failed = [r for r in results if not r["passed"]]
    return {
        "project": str(root),
        "audited_at": datetime.now().isoformat(timespec="seconds"),
        "compliant": not failed,
        "summary": {s: sum(r["severity"] == s for r in failed) for s in SEVERITIES},
        "results": results,
        "disclaimer": "Результат аудита не является сертификацией по ISO/IEC/IEEE 828.",
    }
```

## 5. Результаты запуска
### Тесты (pytest)
```
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-9.2.0, pluggy-1.7.0 -- /Users/wincerdion/Documents/123/scm_practice/.venv/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/wincerdion/Documents/123/scm_practice/config-auditor
configfile: pyproject.toml
testpaths: tests
collecting ... collected 16 items

tests/test_auditor.py::test_compliant_project PASSED                     [  6%]
tests/test_auditor.py::test_missing_required_files PASSED                [ 12%]
tests/test_auditor.py::test_not_a_git_repo_is_critical PASSED            [ 18%]
tests/test_auditor.py::test_too_few_commits PASSED                       [ 25%]
tests/test_auditor.py::test_missing_ci PASSED                            [ 31%]
tests/test_auditor.py::test_bad_version_format[1.0] PASSED               [ 37%]
tests/test_auditor.py::test_bad_version_format[v1.0.0] PASSED            [ 43%]
tests/test_auditor.py::test_bad_version_format[1.0.0-beta] PASSED        [ 50%]
tests/test_auditor.py::test_bad_version_format[latest] PASSED            [ 56%]
tests/test_auditor.py::test_corrupted_pyproject_does_not_crash PASSED    [ 62%]
tests/test_auditor.py::test_missing_project_directory PASSED             [ 68%]
tests/test_auditor.py::test_corrupted_rules_file_falls_back_to_defaults PASSED [ 75%]
tests/test_auditor.py::test_missing_rules_file_warning PASSED            [ 81%]
tests/test_auditor.py::test_custom_rules_change_behaviour PASSED         [ 87%]
tests/test_auditor.py::test_reports_json_and_html PASSED                 [ 93%]
tests/test_auditor.py::test_cli_exit_codes PASSED                        [100%]

============================== 16 passed in 1.94s ==============================
```
### Статический анализ (ruff)
```
All checks passed!
```
### Git: ветки, коммиты, теги
Ветки: main; коммитов: 5; теги: v1.0.0
```
* 70c976c (HEAD -> main, tag: v1.0.0) docs: add CHANGELOG (self-audit passes)
* 65ac168 docs+ci: PRACTICES.md, audit workflow, example reports
* 9a76873 test: 16 tests covering every rule category and corrupted inputs
* da9900f feat: rules loader, checks (files/git/commits/ci/version), JSON+HTML reports, CLI
* ff49da2 chore: init project, README, default rules.json
```

## Подтверждение CI
Workflow-файлы лежат в `.github/workflows/`. Ссылки/скриншоты запусков GitHub Actions обязательны для заданий 5–9 — вставьте их после `git push` в раздел ниже (шаблон — `docs/CI_EVIDENCE.md` там, где он есть):
- Ссылка на репозиторий: _вставить_
- Ссылки на запуски Actions: _вставить_

## 6. Связь с конфигурационным управлением
Аудит конфигурации — проверка того, что проект соблюдает принятые правила (идентификация, версионирование, наличие CI и истории). Поддерживаемые/неподдерживаемые практики — `docs/PRACTICES.md`.

## 7. Ограничения системы
Результат не является сертификацией по ISO/IEC/IEEE 828; проверяется наличие, а не содержание файлов и workflow.

## 8. Вывод
В ходе работы выполнено задание 7: «Аудит конфигурации программного проекта». Функциональные требования реализованы, автоматические тесты проходят, изменения оформлены в Git (ветки, содержательные коммиты, тег). Результаты подтверждают работоспособность решения в пределах перечисленных ограничений.

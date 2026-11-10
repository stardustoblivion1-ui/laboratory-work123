# Отчёт по практической работе №19–20 — задание 8

**Тема:** Комплексная SCM-платформа  
**Репозиторий:** `scm-platform` (локальный Git-репозиторий; ссылка на GitHub — _вставить_)

## 1. Цель работы
Реализовать интегрированную систему управления конфигурацией нескольких проектов: КЕ и версии, запросы с одобрением, неизменяемые baseline, релизы, отчёты.

## 2. Схема алгоритма
```
register_ci → версия 1.0.0
create_change → decide(approve/reject) → apply_change (только approved, версия растёт) → новая версия КЕ
create_baseline: снимок «КЕ→версия» (триггеры БД запрещают UPDATE/DELETE)
register_release: SemVer строго больше предыдущих, ссылка на baseline
```

## 3. Описание архитектуры
`registry.py`, `changes.py`, `baselines.py`, `releases.py`, `db.py` (схемы модулей), `cli.py`. Ветки feature-registry/changes/baselines/release, слияния «Merge pull request #1–#4».

## 4. Основные фрагменты кода
**`src/scmp/changes.py` — `apply_change`**
```python
def apply_change(conn, change_id: int, ci_name: str, new_version: str, content_hash: str) -> None:
    """Создаёт новую версию CI. Допустимо только для одобренного запроса."""
    ch = _get(conn, change_id)
    if ch["status"] != "approved":
        raise ScmError(
            f"Запрос {change_id} нельзя применить: статус «{ch['status']}», требуется «approved»")
    parse_semver(new_version)
    project = conn.execute("SELECT name FROM projects WHERE id=?", (ch["project_id"],)).fetchone()
    cid = ci_id(conn, project["name"], ci_name)
    if parse_semver(new_version) <= parse_semver(current_version(conn, cid)):
        raise ScmError(
            f"Новая версия {new_version} должна быть больше текущей {current_version(conn, cid)}")
    conn.execute("INSERT INTO ci_versions (ci_id, version, content_hash, created_at, change_id) "
                 "VALUES (?,?,?,?,?)", (cid, new_version, content_hash, now(), change_id))
    conn.execute("UPDATE change_requests SET status='applied' WHERE id=?", (change_id,))
    log(conn, ch["project_id"], "change.apply", f"#{change_id} {ci_name}@{new_version}")
    conn.commit()
```

**`src/scmp/baselines.py` — `create_baseline`**
```python
def create_baseline(conn, project: str, name: str) -> int:
    name = require_text(name, "Имя baseline")
    pid = project_id(conn, project)
    items = list_cis(conn, project)
    if not items:
        raise ScmError("Нельзя создать baseline: в проекте нет конфигурационных единиц")
    try:
        cur = conn.execute("INSERT INTO baselines (project_id, name, created_at) VALUES (?,?,?)",
                           (pid, name, now()))
    except sqlite3.IntegrityError:
        raise ScmError(f"Baseline «{name}» уже существует и не может быть изменена") from None
    conn.executemany("INSERT INTO baseline_items (baseline_id, ci_name, version) VALUES (?,?,?)",
                     [(cur.lastrowid, i["name"], i["version"]) for i in items])
    log(conn, pid, "baseline.create", f"{name} ({len(items)} CI)")
    conn.commit()
    return cur.lastrowid
```

**`src/scmp/releases.py` — `register_release`**
```python
def register_release(conn, project: str, version: str, baseline: str) -> int:
    v = parse_semver(version)
    pid = project_id(conn, project)
    bl = get_baseline(conn, project, baseline)
    last = conn.execute("SELECT version FROM releases WHERE project_id=?", (pid,)).fetchall()
    if last and v <= max(parse_semver(r["version"]) for r in last):
        raise ScmError(f"Версия релиза {version} должна быть больше всех предыдущих")
    try:
        cur = conn.execute("INSERT INTO releases (project_id, version, baseline_id, created_at) "
                           "VALUES (?,?,?,?)", (pid, version, bl["id"], now()))
    except sqlite3.IntegrityError:
        raise ScmError(f"Релиз {version} уже зарегистрирован") from None
    log(conn, pid, "release.register", f"{version} on {baseline}")
    conn.commit()
    return cur.lastrowid
```

## 5. Результаты запуска
### Тесты (pytest)
```
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-9.2.0, pluggy-1.7.0 -- /Users/wincerdion/Documents/123/scm_practice/.venv/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/wincerdion/Documents/123/scm_practice/scm-platform
configfile: pyproject.toml
testpaths: tests
collecting ... collected 22 items

tests/test_baselines.py::test_baseline_captures_current_versions PASSED  [  4%]
tests/test_baselines.py::test_baseline_not_affected_by_later_changes PASSED [  9%]
tests/test_baselines.py::test_baseline_is_immutable_in_database PASSED   [ 13%]
tests/test_baselines.py::test_duplicate_baseline_name_rejected PASSED    [ 18%]
tests/test_baselines.py::test_compare_two_baselines PASSED               [ 22%]
tests/test_baselines.py::test_empty_project_and_unknown_baseline PASSED  [ 27%]
tests/test_changes.py::test_approve_and_apply_creates_new_version PASSED [ 31%]
tests/test_changes.py::test_unapproved_change_cannot_be_applied PASSED   [ 36%]
tests/test_changes.py::test_rejected_change_cannot_be_applied PASSED     [ 40%]
tests/test_changes.py::test_decision_only_once_and_requires_person PASSED [ 45%]
tests/test_changes.py::test_applied_change_cannot_be_reused PASSED       [ 50%]
tests/test_changes.py::test_version_must_increase PASSED                 [ 54%]
tests/test_changes.py::test_unknown_change PASSED                        [ 59%]
tests/test_registry.py::test_register_project_and_duplicates PASSED      [ 63%]
tests/test_registry.py::test_register_ci_with_initial_version PASSED     [ 68%]
tests/test_registry.py::test_ci_validation PASSED                        [ 72%]
tests/test_registry.py::test_same_ci_name_in_different_projects PASSED   [ 77%]
tests/test_release_and_e2e.py::test_full_scenario_request_to_release PASSED [ 81%]
tests/test_release_and_e2e.py::test_release_duplicate_and_decrease_rejected PASSED [ 86%]
tests/test_release_and_e2e.py::test_release_needs_existing_baseline_and_valid_version PASSED [ 90%]
tests/test_release_and_e2e.py::test_projects_are_isolated PASSED         [ 95%]
tests/test_release_and_e2e.py::test_cli_scenario_and_errors PASSED       [100%]

============================== 22 passed in 0.16s ==============================
```
### Статический анализ (ruff)
```
All checks passed!
```
### Git: ветки, коммиты, теги
Ветки: feature-baselines, feature-changes, feature-registry, feature-release, main; коммитов: 16; теги: v1.0.0
```
* dbaa169 (HEAD -> main, tag: v1.0.0) docs: CHANGELOG, demo scenario, CI evidence
*   9d25086 Merge pull request #4 from feature-release
|\  
| * 81a2d0f (feature-release) test: end-to-end scenario request->approval->change->baseline->release
| * 0d608e3 feat(cli): scmp command-line interface
| * ac2bda3 feat(release): release registration, history and project report
|/  
*   be56783 Merge pull request #3 from feature-baselines
|\  
| * 5bdfd21 (feature-baselines) test(baselines): immutability, snapshot semantics, comparison
| * d316ca5 feat(baselines): immutable baselines (DB triggers) and comparison
|/  
*   e5c4162 Merge pull request #2 from feature-changes
|\  
| * e4a0a4f (feature-changes) test(changes): approval workflow and guard against unapproved apply
| * 3d9af61 feat(changes): change requests with approval decision and guarded apply
|/  
*   405d200 Merge pull request #1 from feature-registry
|\  
| * 2b7dca7 (feature-registry) feat(registry): projects, configuration items and versions in SQLite
|/  
* a260d7a ci: GitHub Actions (ruff, pytest, build)
* 95bc84c docs: SCMP.md
* f2098a5 chore: init project, README, pyproject
```

## Подтверждение CI
Workflow-файлы лежат в `.github/workflows/`. Ссылки/скриншоты запусков GitHub Actions обязательны для заданий 5–9 — вставьте их после `git push` в раздел ниже (шаблон — `docs/CI_EVIDENCE.md` там, где он есть):
- Ссылка на репозиторий: _вставить_
- Ссылки на запуски Actions: _вставить_

## 6. Связь с конфигурационным управлением
Охвачены идентификация, контроль изменений, baseline, учёт статусов (history), аудит данных отчётом и выпуск. План — SCMP.md; сквозной сценарий — docs/DEMO.md и тест test_full_scenario_request_to_release.

## 7. Ограничения системы
Нет аутентификации и подписи baseline; PR оформлены как merge-коммиты (реальные PR на GitHub создаются после публикации); ссылки на CI — в `docs/CI_EVIDENCE.md`.

## 8. Вывод
В ходе работы выполнено задание 8: «Комплексная SCM-платформа». Функциональные требования реализованы, автоматические тесты проходят, изменения оформлены в Git (ветки, содержательные коммиты, тег). Результаты подтверждают работоспособность решения в пределах перечисленных ограничений.

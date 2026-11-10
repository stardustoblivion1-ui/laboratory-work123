# Отчёт по практической работе №19–20 — задание 2

**Тема:** Журнал изменений проекта  
**Репозиторий:** `change-tracker` (локальный Git-репозиторий; ссылка на GitHub — _вставить_)

## 1. Цель работы
Реализовать регистрацию запросов на изменение с контролем статусов и связью с Git-коммитами.

## 2. Схема алгоритма
```
add: проверка полей → уникальный ID → запись в JSON
set_status: допустим только переход planned→in_progress→done
link_commit: проверка hex-хэша (7–40 символов) → сохранение commit_hash
report: сводка по статусам + список изменений с коммитами
```

## 3. Описание архитектуры
`models.py` — Change, статусы и таблица переходов; `store.py` — ChangeTracker (JSON-хранилище, фильтры); `report.py` — экспорт отчёта (ветка feature-report); `cli.py`.

## 4. Основные фрагменты кода
**`src/tracker/store.py` — `ChangeTracker.set_status`**
```python
    def set_status(self, change_id: str, status: str) -> Change:
        if status not in STATUSES:
            raise TrackerError(f"Некорректный статус {status!r}; допустимо: {', '.join(STATUSES)}")
        ch = self.get(change_id)
        if status not in TRANSITIONS[ch.status]:
            raise TrackerError(f"Переход {ch.status} → {status} недопустим")
        ch.status = status
        self._save()
        return ch
```

**`src/tracker/report.py` — `build_report`**
```python
def build_report(tr: ChangeTracker) -> dict:
    items = [c.to_dict() for c in tr.changes.values()]
    return {
        "total": len(items),
        "by_status": dict(Counter(c["status"] for c in items)),
        "traceable": [{"id": c["id"], "commit_hash": c["commit_hash"]}
                      for c in items if c["commit_hash"]],
        "without_commit": [c["id"] for c in items if not c["commit_hash"]],
        "changes": items,
    }
```

## 5. Результаты запуска
### Тесты (pytest)
```
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-9.2.0, pluggy-1.7.0 -- /Users/wincerdion/Documents/123/scm_practice/.venv/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/wincerdion/Documents/123/scm_practice/change-tracker
configfile: pyproject.toml
testpaths: tests
collecting ... collected 13 items

tests/test_report.py::test_report_summary_and_traceability PASSED        [  7%]
tests/test_report.py::test_export_json_file_and_cli PASSED               [ 15%]
tests/test_report.py::test_cli_reports_errors PASSED                     [ 23%]
tests/test_tracker.py::test_add_generates_unique_ids PASSED              [ 30%]
tests/test_tracker.py::test_duplicate_id_rejected PASSED                 [ 38%]
tests/test_tracker.py::test_valid_transitions PASSED                     [ 46%]
tests/test_tracker.py::test_invalid_transition_rejected PASSED           [ 53%]
tests/test_tracker.py::test_unknown_status_rejected PASSED               [ 61%]
tests/test_tracker.py::test_persistence_after_restart PASSED             [ 69%]
tests/test_tracker.py::test_invalid_type_and_empty_fields PASSED         [ 76%]
tests/test_tracker.py::test_link_commit_validation PASSED                [ 84%]
tests/test_tracker.py::test_corrupted_file PASSED                        [ 92%]
tests/test_tracker.py::test_filtering_by_author_type_status PASSED       [100%]

============================== 13 passed in 0.05s ==============================
```
### Статический анализ (ruff)
```
All checks passed!
```
### Git: ветки, коммиты, теги
Ветки: feature-report, main; коммитов: 7; теги: v1.0.0
```
* 3f939e6 (HEAD -> main, tag: v1.0.0) docs: CHANGELOG with ID↔commit examples, example journal
*   db3d8fb Merge branch 'feature-report' into main
|\  
| * fd3eb08 (feature-report) feat(report): JSON export with status summary and commit traceability
|/  
* 918573e feat: command-line interface
* 866f6d2 test: filtering by author, type and status
* cbc9794 feat: change model, statuses and JSON-persistent tracker
* a6df276 chore: init project, README, pyproject
```

## 6. Связь с конфигурационным управлением
Журнал — реализация учёта запросов на изменение и статусов; поле commit_hash даёт прослеживаемость «ID изменения ↔ коммит» (примеры в CHANGELOG.md и examples/changes.json).

## 7. Ограничения системы
JSON-файл без блокировок; нет ролей и решения об одобрении; хэш проверяется по формату, а не по репозиторию.

## 8. Вывод
В ходе работы выполнено задание 2: «Журнал изменений проекта». Функциональные требования реализованы, автоматические тесты проходят, изменения оформлены в Git (ветки, содержательные коммиты, тег). Результаты подтверждают работоспособность решения в пределах перечисленных ограничений.

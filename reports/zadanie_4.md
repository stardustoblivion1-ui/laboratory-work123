# Отчёт по практической работе №19–20 — задание 4

**Тема:** Управление задачами и конфликтами Git  
**Репозиторий:** `team-tasks` (локальный Git-репозиторий; ссылка на GitHub — _вставить_)

## 1. Цель работы
Разработать менеджер задач на SQLite и продемонстрировать контролируемый конфликт слияния и его разрешение.

## 2. Схема алгоритма
```
CRUD: валидация → SQL с параметрами → commit
filter: условия по исполнителю/приоритету/статусу объединяются через И
stats: подсчёт всего/выполнено/по статусам и исполнителям
Конфликт: feature-filter и feature-statistics правят одни и те же строки cli.py и FEATURES.md → merge → ручное разрешение с сохранением обеих функций
```

## 3. Описание архитектуры
`db.py` — TaskDB (SQLite, валидация); `filters.py`; `stats.py`; `cli.py` с маркерами расширения. Ветки: feature-tasks, feature-filter, feature-statistics.

## 4. Основные фрагменты кода
**`src/taskman/db.py` — `TaskDB.update`**
```python
    def update(self, task_id: int, **fields) -> dict:
        fields = {k: v for k, v in fields.items() if v is not None}
        unknown = set(fields) - {"title", "assignee", "priority", "status", "due"}
        if unknown:
            raise TaskError(f"Неизвестные поля: {', '.join(sorted(unknown))}")
        self.get(task_id)
        validate(**fields)
        if fields:
            sets = ", ".join(f"{k}=?" for k in fields)
            self.conn.execute(f"UPDATE tasks SET {sets} WHERE id=?", (*fields.values(), task_id))
            self.conn.commit()
        return self.get(task_id)
```

**`src/taskman/filters.py` — `filter_tasks`**
```python
def filter_tasks(db: TaskDB, assignee=None, priority=None, status=None) -> list[dict]:
    return [t for t in db.all()
            if (assignee is None or t["assignee"] == assignee)
            and (priority is None or t["priority"] == priority)
            and (status is None or t["status"] == status)]
```

**`src/taskman/stats.py` — `statistics`**
```python
def statistics(db: TaskDB) -> dict:
    tasks = db.all()
    total = len(tasks)
    done = sum(t["status"] == "done" for t in tasks)
    return {
        "total": total,
        "done": done,
        "percent_done": round(100 * done / total, 1) if total else 0.0,
        "by_status": dict(Counter(t["status"] for t in tasks)),
        "by_assignee": dict(Counter(t["assignee"] for t in tasks)),
    }
```

## 5. Результаты запуска
### Тесты (pytest)
```
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-9.2.0, pluggy-1.7.0 -- /Users/wincerdion/Documents/123/scm_practice/.venv/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/wincerdion/Documents/123/scm_practice/team-tasks
configfile: pyproject.toml
testpaths: tests
collecting ... collected 17 items

tests/test_after_merge.py::test_both_commands_registered PASSED          [  5%]
tests/test_after_merge.py::test_filter_and_stats_work_together PASSED    [ 11%]
tests/test_after_merge.py::test_features_file_lists_all_functions PASSED [ 17%]
tests/test_after_merge.py::test_invalid_input_still_rejected PASSED      [ 23%]
tests/test_after_merge.py::test_empty_db_commands[list] PASSED           [ 29%]
tests/test_after_merge.py::test_empty_db_commands[stats] PASSED          [ 35%]
tests/test_after_merge.py::test_empty_db_commands[filter] PASSED         [ 41%]
tests/test_crud.py::test_add_and_get PASSED                              [ 47%]
tests/test_crud.py::test_update_and_delete PASSED                        [ 52%]
tests/test_crud.py::test_validation_errors PASSED                        [ 58%]
tests/test_crud.py::test_persistence_after_restart PASSED                [ 64%]
tests/test_filters.py::test_filter_by_each_field PASSED                  [ 70%]
tests/test_filters.py::test_filter_combined_and_empty PASSED             [ 76%]
tests/test_filters.py::test_cli_filter PASSED                            [ 82%]
tests/test_stats.py::test_empty_statistics PASSED                        [ 88%]
tests/test_stats.py::test_statistics_counts PASSED                       [ 94%]
tests/test_stats.py::test_cli_stats PASSED                               [100%]

============================== 17 passed in 0.05s ==============================
```
### Статический анализ (ruff)
```
All checks passed!
```
### Git: ветки, коммиты, теги
Ветки: feature-filter, feature-statistics, feature-tasks, main; коммитов: 9; теги: v1.0.0
```
* f763d06 (HEAD -> main, tag: v1.0.0) style: fix ruff SIM115 in tests
* 6c3e198 docs: conflict resolution report
*   ceb26d4 Merge branch 'feature-statistics' (resolved conflicts in cli.py and FEATURES.md, kept both features)
|\  
| * b6edc0a (feature-statistics) feat(statistics): completion statistics command
* |   2d5cfad Merge branch 'feature-filter'
|\ \  
| |/  
|/|   
| * eb3390a (feature-filter) feat(filter): filter tasks by assignee, priority and status
|/  
*   098ec59 Merge branch 'feature-tasks'
|\  
| * 9502444 (feature-tasks) feat(tasks): SQLite CRUD with validation and CLI
|/  
* d0bb952 chore: init project, README, FEATURES.md
```

## 6. Связь с конфигурационным управлением
Показан процесс контролируемого слияния: независимые изменения, обнаружение конфликта, разрешение без потери функций, итоговый merge-коммит и тесты после слияния. Подробности и вывод git — `docs/CONFLICT_REPORT.md`.

## 7. Ограничения системы
Нет многопользовательского доступа и аутентификации; даты хранятся как ISO-строки.

## 8. Вывод
В ходе работы выполнено задание 4: «Управление задачами и конфликтами Git». Функциональные требования реализованы, автоматические тесты проходят, изменения оформлены в Git (ветки, содержательные коммиты, тег). Результаты подтверждают работоспособность решения в пределах перечисленных ограничений.

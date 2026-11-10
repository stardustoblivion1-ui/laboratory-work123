# team-tasks

Менеджер командных задач (практическая работа №19–20, задание 4): SQLite, CRUD, фильтры, статистика.

```bash
pip install -r requirements.txt && pip install -e .
team-tasks add "Написать тесты" --assignee Ivan --priority high --due 2026-12-01
team-tasks list
team-tasks update 1 --status done
team-tasks filter --assignee Ivan --priority high --status todo
team-tasks stats
team-tasks delete 1
pytest -v
```
БД по умолчанию — `tasks.db` (`--db путь`). История слияния и конфликта — `docs/CONFLICT_REPORT.md`.

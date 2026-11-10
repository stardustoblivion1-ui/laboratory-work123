# change-tracker

Журнал запросов на изменение (практическая работа №19–20, задание 2).

```bash
pip install -r requirements.txt && pip install -e .
change-tracker add --author Ivan --type feature --desc "Добавить экспорт"
change-tracker status CH-001 in_progress
change-tracker link CH-001 <git-commit-hash>
change-tracker list --author Ivan --status done
change-tracker report out.json
pytest -v
```
Статусы: `planned → in_progress → done` (другие переходы запрещены).
Данные хранятся в `changes.json` (путь задаётся `--db`).

# Подтверждение работы CI

Workflow: `.github/workflows/ci.yml` (push, pull_request; Python 3.11 и 3.12; ruff + pytest).

| Запуск | Коммит | Ожидаемый результат | Причина |
|---|---|---|---|
| 1 (намеренно неуспешный) | `985f57fd596b7dddbba846b120866861b02c142e` | ❌ шаг «Lint (ruff)» падает | F401: неиспользуемый `import os` в `src/warehouse/db.py` |
| 2 (успешный) | `41fa5cf76e601820672f6acf4bfe0c965dbadb5e` | ✅ ruff и pytest проходят | импорт удалён отдельным коммитом-исправлением |

Локальная проверка обоих состояний: `git checkout 985f57fd596b7dddbba846b120866861b02c142e && ruff check .` (ошибка) и `git checkout 41fa5cf76e601820672f6acf4bfe0c965dbadb5e && ruff check . && pytest` (успех).

## Ссылки на запуски GitHub Actions
После `git push` в GitHub-репозиторий вставьте сюда ссылки на запуски (вкладка Actions):
- Неуспешный запуск: _ссылка_
- Успешный запуск: _ссылка_

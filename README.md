# scm-platform

Интегрированная система управления конфигурацией нескольких проектов (практическая работа №19–20, задание 8).
SQLite + консольный интерфейс. Подробности процессов — `SCMP.md`.

```bash
pip install -r requirements.txt && pip install -e .
scmp project add shop
scmp ci add shop api                       # конфигурационная единица, версия 1.0.0
scmp change create shop "Новый эндпоинт" -d "Добавить /orders"
scmp change decide 1 approve --by "Иванов" --note "ок"
scmp change apply 1 api 1.1.0 --hash abc123   # применить можно только одобренный запрос
scmp baseline create shop BL-1                # неизменяемая baseline
scmp baseline compare shop BL-1 BL-2
scmp release register shop 1.0.0 --baseline BL-1
scmp report shop
scmp history shop
pytest -v
```
Все команды принимают `--db файл.db` (по умолчанию `scmp.db`).

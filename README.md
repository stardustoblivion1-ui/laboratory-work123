# warehouse-ci

Складской учёт (SQLite) с непрерывной интеграцией GitHub Actions (практическая работа №19–20, задание 5).

```bash
pip install -r requirements.txt && pip install -e .
warehouse category add Инструменты
warehouse product add Молоток --category Инструменты --qty 10
warehouse receive Молоток 5 --note "поставка"
warehouse issue Молоток 3
warehouse search мол
warehouse report
warehouse journal
pytest -v && ruff check .
```
CI: `.github/workflows/ci.yml` — на `push` и `pull_request`, Python 3.11 и 3.12, шаги `ruff check .` и `pytest -v`.
Подтверждения запусков CI (два run'а: неуспешный и успешный) — в `docs/CI_EVIDENCE.md`.

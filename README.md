# config-control

Инструмент обнаружения расхождений между файлами проекта и утверждённой baseline
(практическая работа №19–20, задание 3). Правила — в `CONFIGURATION_MANAGEMENT.md`.

```bash
pip install -r requirements.txt && pip install -e .
cfgctl baseline <каталог> --by "Иванов И.И." [--previous BL-0001]   # создать новую baseline
cfgctl check <каталог> --baseline baselines/BL-0001.json --report report.json
pytest -v
```
Код возврата `check`: 0 — расхождений нет, 1 — есть расхождения, 2 — ошибка (например, нет baseline).

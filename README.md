# config-auditor

Конфигурируемый аудитор правил проекта (практическая работа №19–20, задание 7).
Проверяет: наличие README.md / CHANGELOG.md / pyproject.toml, Git-репозитория и CI workflow, формат версии (MAJOR.MINOR.PATCH), минимальное число коммитов.
Правила — в `rules.json`; результат — отчёты JSON и HTML с уровнем критичности (`critical/high/medium/low`).

```bash
pip install -r requirements.txt && pip install -e .
auditor audit <каталог_проекта> --rules rules.json --json report.json --html report.html
pytest -v
```
Код возврата: 0 — нарушений нет, 1 — есть нарушения. Аудитор не падает на отсутствующих или повреждённых файлах — они фиксируются как нарушения.
Что поддерживается и что нет — `docs/PRACTICES.md`. **Результат аудита не является сертификацией по ISO/IEC/IEEE 828.**

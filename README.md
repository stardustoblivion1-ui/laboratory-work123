# scm-traceability

Инструмент доказательного контроля изменений одного Python-проекта (практическая работа №19–20, задание 9).
Главный результат — **матрица прослеживаемости** «процесс → правило SCMP → функция → тест → доказательство» и
цепочка «ID запроса → решение → коммит → baseline → тест → отчёт».

```bash
pip install -r requirements.txt && pip install -e .
trace ci-add src/trace/registry.py --version 1.0.0            # регистрация КЕ (SQLite-реестр)
trace request-create CI-001 "Рефакторинг реестра" 1.1.0       # запрос на изменение
trace decide CR-001 approve --by "Иванов" --note "ок"         # решение
trace apply CR-001                                            # применить можно только одобренное
trace link CR-001 --commit <hash> --test tests/test_registry.py::test_apply_updates_version_and_hash
trace baseline                                                # неизменяемая baseline
trace verify BL-001                                           # baseline обнаруживает изменения файлов
trace audit --report audit.json                               # аудит и JSON-отчёт
trace matrix --out docs/TRACEABILITY_MATRIX.md                # матрица и статусы процессов
trace chain CR-001                                            # демонстрация цепочки
pytest -v
```
Опции `--db` (по умолчанию `trace.db`) и `--root` (корень проекта, по умолчанию `.`).

Документы: `SCMP.md`, `docs/TRACEABILITY_MATRIX.md`, `docs/ANALYTICAL_CONCLUSION.md`, `docs/DEMO.md`, `CHANGELOG.md`.
**Полное соответствие ISO/IEC/IEEE 828 не заявляется** (стандарт — Inactive-Reserved, используется как учебная основа).

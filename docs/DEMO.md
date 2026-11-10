# Демонстрация цепочки: ID запроса → решение → коммит → baseline → тест → отчёт

```
$ scmtrace ci-add README.md
КЕ зарегистрирована: CI-001
$ scmtrace request-create CI-001 Добавить в README раздел о демонстрации 1.1.0
Создан запрос: CR-001
$ scmtrace apply CR-001
Ошибка: Запрос CR-001 нельзя применить: статус «proposed», нужен «approved»
$ scmtrace decide CR-001 approve --by Иванов И.И. --note Согласовано CCB
Статус: approved
$ scmtrace apply CR-001
Запрос применён: CR-001
$ scmtrace link CR-001 --commit 7a632fd4cbc785bad12407cdd74ecc3131567a91 --test tests/test_registry.py::test_apply_updates_version_and_hash
{'id': 'CR-001', 'ci_id': 'CI-001', 'title': 'Добавить в README раздел о демонстрации', 'new_version': '1.1.0', 'status': 'applied', 'created_at': '2026-11-10T17:03:47', 'commit_hash': '7a632fd4cbc785bad12407cdd74ecc3131567a91', 'baseline_id': None, 'test_ref': 'tests/test_registry.py::test_apply_updates_version_and_hash'}
$ scmtrace baseline
Baseline создана: BL-001
$ scmtrace verify BL-001
{
  "baseline": "BL-001",
  "ok": true,
  "modified": [],
  "missing": []
}
$ scmtrace audit --report examples/audit_report.json
Аудит: соответствует; отчёт → examples/audit_report.json
$ scmtrace chain CR-001 --report examples/audit_report.json
1. Запрос      CR-001: Добавить в README раздел о демонстрации (CI-001 → 1.1.0, статус applied)
2. Решение     одобрено — Иванов И.И. (2026-11-10T17:03:47) Согласовано CCB
3. Коммит      7a632fd4cbc785bad12407cdd74ecc3131567a91 (в истории Git: да)
4. Baseline    BL-001
5. Тест        tests/test_registry.py::test_apply_updates_version_and_hash
6. Отчёт       examples/audit_report.json
```

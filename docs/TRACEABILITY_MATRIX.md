# Матрица прослеживаемости

| Процесс | Правило SCMP | Функция | Тест | Доказательство | Статус |
|---|---|---|---|---|---|
| Идентификация конфигурационных единиц | SCMP-3 | `scmtrace.registry.Registry.register_ci` ✅ | `tests/test_registry.py::test_register_ci_records_path_version_sha` ✅ | SCMP.md ✅ | **реализован** |
| Согласование изменений (CCB) | SCMP-4 | `scmtrace.registry.Registry.decide` ✅ | `tests/test_registry.py::test_approve_and_reject` ✅ | docs/DEMO.md ✅ | **реализован** |
| Запрет неодобренных изменений | SCMP-4 | `scmtrace.registry.Registry.apply` ✅ | `tests/test_registry.py::test_unapproved_change_forbidden` ✅ | docs/DEMO.md ✅ | **реализован** |
| Связь запрос ↔ Git-коммит ↔ тест | SCMP-5 | `scmtrace.audit.audit` ✅ | `tests/test_audit.py::test_audit_detects_unknown_commit_hash` ✅ | examples/audit_report.json ✅ | **реализован** |
| Baseline и контроль целостности | SCMP-6 | `scmtrace.baseline.verify_baseline` ✅ | `tests/test_registry.py::test_baseline_create_and_verify_detects_changes` ✅ | docs/DEMO.md ✅ | **реализован** |
| Учёт статусов конфигурации | SCMP-7 | `scmtrace.audit.build_report` ✅ | `tests/test_audit.py::test_report_json_written_with_baseline_checks` ✅ | examples/audit_report.json ✅ | **частично** |
| Аудит конфигурации | SCMP-8 | `scmtrace.audit.audit` ✅ | `tests/test_audit.py::test_audit_detects_unapproved_file_change` ✅ | examples/audit_report.json ✅ | **частично** |
| Управление выпуском | SCMP-9 | `—` ❌ | `—` ❌ | CHANGELOG.md ❌ | **не реализован** |

## Ограничения по процессам

- **Идентификация конфигурационных единиц** (реализован): Единицы регистрируются вручную; нет автообнаружения новых файлов.
- **Согласование изменений (CCB)** (реализован): Лицо, принимающее решение, — строка без аутентификации.
- **Запрет неодобренных изменений** (реализован): Блокируется только фиксация в реестре; запретить правку файла в Git инструмент не может — она обнаруживается аудитом.
- **Связь запрос ↔ Git-коммит ↔ тест** (реализован): Проверяется существование коммита, а не то, что он содержит именно это изменение.
- **Baseline и контроль целостности** (реализован): Неизменяемость обеспечена триггерами SQLite, но файл БД можно заменить целиком.
- **Учёт статусов конфигурации** (частично): Есть статусы запросов и сводка, но нет истории переходов по времени и отчётов о статусе по запросу.
- **Аудит конфигурации** (частично): Проверяется формальное соответствие; нет аудита содержания документов и физического аудита.
- **Управление выпуском** (не реализован): Выпуск делается вручную (Git-тег + CHANGELOG); автоматизации нет (см. проекты release-manager и scm-platform).

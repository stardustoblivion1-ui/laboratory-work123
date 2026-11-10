# Отчёт по практической работе №19–20 — задание 9

**Тема:** Прослеживаемость процессов ISO/IEC/IEEE 828  
**Репозиторий:** `scm-traceability` (локальный Git-репозиторий; ссылка на GitHub — _вставить_)

## 1. Цель работы
Разработать инструмент доказательного контроля изменений: реестр КЕ, запросов и решений, связи с Git, baseline, аудит и матрица прослеживаемости.

## 2. Схема алгоритма
```
apply: статус approved? → пересчитать SHA-256 файла → обновить версию КЕ → статус applied
audit: хэши КЕ = файлы? для applied: решение, commit в git, baseline, тест
matrix: для каждой строки проверить существование функции, теста и файла-доказательства
chain: ID запроса → решение → коммит → baseline → тест → отчёт
```

## 3. Описание архитектуры
`registry.py`, `baseline.py`, `audit.py`, `matrix.py`, `chain.py`, `cli.py`; SCMP.md; docs/TRACEABILITY_MATRIX.md; docs/ANALYTICAL_CONCLUSION.md. Ветки feature-registry, feature-audit, feature-matrix.

## 4. Основные фрагменты кода
**`src/scmtrace/registry.py` — `Registry.apply`**
```python
    def apply(self, cr_id: str, root: str | Path) -> None:
        """Фиксирует в реестре новую версию и SHA-256 КЕ. Только для одобренного запроса."""
        cr = self.get_request(cr_id)
        if cr["status"] != "approved":
            raise TraceError(f"Запрос {cr_id} нельзя применить: статус «{cr['status']}», нужен «approved»")
        ci = self.get_ci(cr["ci_id"])
        f = Path(root) / ci["path"]
        if not f.is_file():
            raise TraceError(f"Файл не найден: {ci['path']}")
        self.conn.execute("UPDATE ci SET version=?, sha256=? WHERE id=?",
                          (cr["new_version"], sha256_of(f), ci["id"]))
        self.conn.execute("UPDATE change_requests SET status='applied' WHERE id=?", (cr_id,))
        self.conn.commit()
```

**`src/scmtrace/audit.py` — `audit`**
```python
def audit(reg, root: str | Path) -> list[dict]:
    findings: list[dict] = []
    for ci in reg.list_ci():
        f = Path(root) / ci["path"]
        if not f.is_file():
            findings.append(_f("ci_file", ci["id"], False, f"Файл {ci['path']} отсутствует"))
        elif sha256_of(f) != ci["sha256"]:
            findings.append(_f("ci_file", ci["id"], False,
                               f"Файл {ci['path']} изменён без одобренного и применённого запроса"))
        else:
            findings.append(_f("ci_file", ci["id"], True, f"{ci['path']} соответствует реестру"))
    for cr in reg.list_requests():
        if cr["status"] != "applied":
            continue
        d = reg.get_decision(cr["id"])
        findings.append(_f("approval", cr["id"], bool(d and d["approved"]),
                           "Есть решение об одобрении" if d and d["approved"]
                           else "Применённый запрос без решения об одобрении"))
        if not cr["commit_hash"]:
            findings.append(_f("git_commit", cr["id"], False, "Не указан commit hash"))
        else:
            ok = commit_exists(root, cr["commit_hash"])
            findings.append(_f("git_commit", cr["id"], ok,
                               f"Коммит {cr['commit_hash'][:10]} найден в истории Git" if ok
                               else f"Коммит {cr['commit_hash'][:10]} не найден в истории Git"))
        findings.append(_f("baseline", cr["id"], bool(cr["baseline_id"]),
                           f"Включён в {cr['baseline_id']}" if cr["baseline_id"]
                           else "Изменение не включено ни в одну baseline"))
        findings.append(_f("test", cr["id"], bool(cr["test_ref"]),
                           f"Тест: {cr['test_ref']}" if cr["test_ref"] else "Не указан тест"))
    return findings
```

**`src/scmtrace/matrix.py` — `build_matrix`**
```python
def build_matrix(root: str | Path = ".") -> list[dict]:
    """Каждую ссылку (функция, тест, доказательство) проверяет на существование."""
    root = Path(root)
    rows = []
    for p in PROCESSES:
        rows.append({**p,
                     "function_ok": _function_exists(p["function"]),
                     "test_ok": _test_exists(root, p["test"]),
                     "evidence_ok": (root / p["evidence"]).exists()})
    return rows
```

## 5. Результаты запуска
### Тесты (pytest)
```
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-9.2.0, pluggy-1.7.0 -- /Users/wincerdion/Documents/123/scm_practice/.venv/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/wincerdion/Documents/123/scm_practice/scm-traceability
configfile: pyproject.toml
testpaths: tests
collecting ... collected 24 items

tests/test_audit.py::test_audit_passes_for_complete_chain PASSED         [  4%]
tests/test_audit.py::test_audit_detects_unapproved_file_change PASSED    [  8%]
tests/test_audit.py::test_audit_detects_unknown_commit_hash PASSED       [ 12%]
tests/test_audit.py::test_audit_requires_commit_baseline_and_test PASSED [ 16%]
tests/test_audit.py::test_report_json_written_with_baseline_checks PASSED [ 20%]
tests/test_audit.py::test_commit_exists_helper PASSED                    [ 25%]
tests/test_matrix_chain_cli.py::test_matrix_references_are_all_real_except_unimplemented PASSED [ 29%]
tests/test_matrix_chain_cli.py::test_matrix_markdown_and_degree PASSED   [ 33%]
tests/test_matrix_chain_cli.py::test_chain_for_full_cycle PASSED         [ 37%]
tests/test_matrix_chain_cli.py::test_chain_without_links PASSED          [ 41%]
tests/test_matrix_chain_cli.py::test_cli_full_flow_and_exit_codes PASSED [ 45%]
tests/test_matrix_chain_cli.py::test_cli_matrix_output_file PASSED       [ 50%]
tests/test_matrix_chain_cli.py::test_cli_unknown_request[bad0] PASSED    [ 54%]
tests/test_matrix_chain_cli.py::test_cli_unknown_request[bad1] PASSED    [ 58%]
tests/test_registry.py::test_register_ci_records_path_version_sha PASSED [ 62%]
tests/test_registry.py::test_register_ci_errors PASSED                   [ 66%]
tests/test_registry.py::test_change_version_through_approved_request PASSED [ 70%]
tests/test_registry.py::test_apply_updates_version_and_hash PASSED       [ 75%]
tests/test_registry.py::test_approve_and_reject PASSED                   [ 79%]
tests/test_registry.py::test_unapproved_change_forbidden PASSED          [ 83%]
tests/test_registry.py::test_request_validation PASSED                   [ 87%]
tests/test_registry.py::test_baseline_create_and_verify_detects_changes PASSED [ 91%]
tests/test_registry.py::test_baseline_immutable PASSED                   [ 95%]
tests/test_registry.py::test_baseline_requires_ci_and_exists PASSED      [100%]

============================== 24 passed in 0.88s ==============================
```
### Статический анализ (ruff)
```
All checks passed!
```
### Git: ветки, коммиты, теги
Ветки: feature-audit, feature-matrix, feature-registry, main; коммитов: 18; теги: v1.0.0
```
* 4dd385f (HEAD -> main, tag: v1.0.0) docs: analytical conclusion and CHANGELOG
* 8b3d53d docs: demo of full traceability chain, matrix and audit report
* 7a632fd docs: add demo section to README (CR-001)
*   e46a7a2 Merge pull request #3 from feature-matrix
|\  
| * 4932390 (feature-matrix) test(matrix): matrix existence checks, chain and CLI flow tests
| * 14a89ed feat(cli): scmtrace commands and request->report chain view
| * 1672299 feat(matrix): traceability matrix with existence checks and process statuses
|/  
*   1796fa8 Merge pull request #2 from feature-audit
|\  
| * 69ff72f (feature-audit) test(audit): audit scenarios, unapproved change and missing commit detection
| * 0d3b76b feat(audit): configuration audit with Git history check and JSON report
| * ca6e7ee fix: console script name scmtrace, README paths
|/  
*   ec58b34 Merge pull request #1 from feature-registry
|\  
| * 374754d (feature-registry) feat(registry): registry tests; rename package to scmtrace (avoid stdlib 'trace' clash)
| * de458d5 feat(baseline): immutable baselines and verification against files
| * 5ad31e6 feat(registry): CI registry, change requests, decisions, approval-guarded apply
|/  
* 50484f5 ci: pytest on push and pull_request
* 7de3f74 docs: SCMP.md
* 5904b98 chore: init project, README, pyproject
```

## Подтверждение CI
Workflow-файлы лежат в `.github/workflows/`. Ссылки/скриншоты запусков GitHub Actions обязательны для заданий 5–9 — вставьте их после `git push` в раздел ниже (шаблон — `docs/CI_EVIDENCE.md` там, где он есть):
- Ссылка на репозиторий: _вставить_
- Ссылки на запуски Actions: _вставить_

## 6. Связь с конфигурационным управлением
Прямая реализация требований прослеживаемости: каждое изменение связано с запросом, решением, коммитом, baseline, тестом и отчётом; для каждого процесса указан статус (реализован / частично / не реализован) и ограничения. Полное соответствие стандарту не заявляется.

## 7. Ограничения системы
См. docs/ANALYTICAL_CONCLUSION.md: нет аутентификации, подписи baseline, истории статусов; выпуск не автоматизирован.

## 8. Вывод
В ходе работы выполнено задание 9: «Прослеживаемость процессов ISO/IEC/IEEE 828». Функциональные требования реализованы, автоматические тесты проходят, изменения оформлены в Git (ветки, содержательные коммиты, тег). Результаты подтверждают работоспособность решения в пределах перечисленных ограничений.

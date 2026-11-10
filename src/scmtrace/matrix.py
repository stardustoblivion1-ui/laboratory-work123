"""Матрица прослеживаемости «процесс → правило SCMP → функция → тест → доказательство»."""
from __future__ import annotations

import importlib
from pathlib import Path

IMPLEMENTED, PARTIAL, MISSING = "реализован", "частично", "не реализован"

PROCESSES = [
    {"process": "Идентификация конфигурационных единиц", "rule": "SCMP-3",
     "function": "scmtrace.registry.Registry.register_ci",
     "test": "tests/test_registry.py::test_register_ci_records_path_version_sha",
     "evidence": "SCMP.md", "status": IMPLEMENTED,
     "limitation": "Единицы регистрируются вручную; нет автообнаружения новых файлов."},
    {"process": "Согласование изменений (CCB)", "rule": "SCMP-4",
     "function": "scmtrace.registry.Registry.decide",
     "test": "tests/test_registry.py::test_approve_and_reject",
     "evidence": "docs/DEMO.md", "status": IMPLEMENTED,
     "limitation": "Лицо, принимающее решение, — строка без аутентификации."},
    {"process": "Запрет неодобренных изменений", "rule": "SCMP-4",
     "function": "scmtrace.registry.Registry.apply",
     "test": "tests/test_registry.py::test_unapproved_change_forbidden",
     "evidence": "docs/DEMO.md", "status": IMPLEMENTED,
     "limitation": "Блокируется только фиксация в реестре; запретить правку файла в Git инструмент не может — она обнаруживается аудитом."},
    {"process": "Связь запрос ↔ Git-коммит ↔ тест", "rule": "SCMP-5",
     "function": "scmtrace.audit.audit",
     "test": "tests/test_audit.py::test_audit_detects_unknown_commit_hash",
     "evidence": "examples/audit_report.json", "status": IMPLEMENTED,
     "limitation": "Проверяется существование коммита, а не то, что он содержит именно это изменение."},
    {"process": "Baseline и контроль целостности", "rule": "SCMP-6",
     "function": "scmtrace.baseline.verify_baseline",
     "test": "tests/test_registry.py::test_baseline_create_and_verify_detects_changes",
     "evidence": "docs/DEMO.md", "status": IMPLEMENTED,
     "limitation": "Неизменяемость обеспечена триггерами SQLite, но файл БД можно заменить целиком."},
    {"process": "Учёт статусов конфигурации", "rule": "SCMP-7",
     "function": "scmtrace.audit.build_report",
     "test": "tests/test_audit.py::test_report_json_written_with_baseline_checks",
     "evidence": "examples/audit_report.json", "status": PARTIAL,
     "limitation": "Есть статусы запросов и сводка, но нет истории переходов по времени и отчётов о статусе по запросу."},
    {"process": "Аудит конфигурации", "rule": "SCMP-8",
     "function": "scmtrace.audit.audit",
     "test": "tests/test_audit.py::test_audit_detects_unapproved_file_change",
     "evidence": "examples/audit_report.json", "status": PARTIAL,
     "limitation": "Проверяется формальное соответствие; нет аудита содержания документов и физического аудита."},
    {"process": "Управление выпуском", "rule": "SCMP-9",
     "function": "—", "test": "—", "evidence": "CHANGELOG.md", "status": MISSING,
     "limitation": "Выпуск делается вручную (Git-тег + CHANGELOG); автоматизации нет (см. проекты release-manager и scm-platform)."},
]


def _function_exists(dotted: str) -> bool:
    if dotted == "—":
        return False
    parts = dotted.split(".")
    for i in range(len(parts) - 1, 0, -1):
        try:
            obj = importlib.import_module(".".join(parts[:i]))
        except ImportError:
            continue
        for name in parts[i:]:
            obj = getattr(obj, name, None)
            if obj is None:
                return False
        return True
    return False


def _test_exists(root: Path, ref: str) -> bool:
    if ref == "—" or "::" not in ref:
        return False
    file, name = ref.split("::", 1)
    f = root / file
    return f.is_file() and f"def {name}(" in f.read_text(encoding="utf-8")


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


def render_markdown(rows: list[dict]) -> str:
    mark = lambda ok: "✅" if ok else "❌"
    out = ["# Матрица прослеживаемости", "",
           "| Процесс | Правило SCMP | Функция | Тест | Доказательство | Статус |",
           "|---|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r['process']} | {r['rule']} | `{r['function']}` {mark(r['function_ok'])} | "
                   f"`{r['test']}` {mark(r['test_ok'])} | {r['evidence']} {mark(r['evidence_ok'])} | "
                   f"**{r['status']}** |")
    out += ["", "## Ограничения по процессам", ""]
    out += [f"- **{r['process']}** ({r['status']}): {r['limitation']}" for r in rows]
    return "\n".join(out) + "\n"


def degree(rows: list[dict]) -> dict:
    n = len(rows)
    cnt = {s: sum(r["status"] == s for r in rows) for s in (IMPLEMENTED, PARTIAL, MISSING)}
    score = (cnt[IMPLEMENTED] + 0.5 * cnt[PARTIAL]) / n
    return {"processes": n, **cnt, "score_percent": round(100 * score)}

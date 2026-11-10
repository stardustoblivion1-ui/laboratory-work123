"""Аудит конфигурации и JSON-отчёт."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

from .baseline import verify_baseline
from .registry import sha256_of


def commit_exists(root: str | Path, commit_hash: str) -> bool:
    try:
        r = subprocess.run(["git", "-C", str(root), "cat-file", "-e", f"{commit_hash}^{{commit}}"],
                           capture_output=True, check=False)
    except OSError:
        return False
    return r.returncode == 0


def _f(check: str, subject: str, ok: bool, message: str) -> dict:
    return {"check": check, "subject": subject, "ok": ok, "message": message}


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


def build_report(reg, root: str | Path) -> dict:
    findings = audit(reg, root)
    baselines = [r["id"] for r in reg.conn.execute("SELECT id FROM baselines ORDER BY id")]
    by_status: dict[str, int] = {}
    for cr in reg.list_requests():
        by_status[cr["status"]] = by_status.get(cr["status"], 0) + 1
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "compliant": all(f["ok"] for f in findings),
        "requests_by_status": by_status,
        "baseline_checks": [verify_baseline(reg, b, root) for b in baselines],
        "findings": findings,
        "failed": [f for f in findings if not f["ok"]],
    }


def write_report(reg, root: str | Path, out: str | Path) -> dict:
    rep = build_report(reg, root)
    Path(out).write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    return rep

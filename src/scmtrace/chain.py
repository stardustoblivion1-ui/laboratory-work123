"""Цепочка: ID запроса → решение → коммит → baseline → тест → отчёт."""
from __future__ import annotations

from .audit import commit_exists


def build_chain(reg, root, cr_id: str, report_path: str = "audit_report.json") -> dict:
    cr = reg.get_request(cr_id)
    d = reg.get_decision(cr_id)
    return {
        "request": {"id": cr["id"], "title": cr["title"], "ci": cr["ci_id"],
                    "new_version": cr["new_version"], "status": cr["status"]},
        "decision": ({"approved": bool(d["approved"]), "by": d["decided_by"], "note": d["note"],
                      "at": d["decided_at"]} if d else None),
        "commit": ({"hash": cr["commit_hash"], "in_git_history": commit_exists(root, cr["commit_hash"])}
                   if cr["commit_hash"] else None),
        "baseline": cr["baseline_id"],
        "test": cr["test_ref"],
        "report": report_path,
    }


def render(chain: dict) -> str:
    r, d, c = chain["request"], chain["decision"], chain["commit"]
    lines = [
        f"1. Запрос      {r['id']}: {r['title']} ({r['ci']} → {r['new_version']}, статус {r['status']})",
        "2. Решение     " + (f"{'одобрено' if d['approved'] else 'отклонено'} — {d['by']} ({d['at']}) {d['note']}"
                            if d else "— нет —"),
        "3. Коммит      " + (f"{c['hash']} (в истории Git: {'да' if c['in_git_history'] else 'НЕТ'})"
                            if c else "— нет —"),
        f"4. Baseline    {chain['baseline'] or '— нет —'}",
        f"5. Тест        {chain['test'] or '— нет —'}",
        f"6. Отчёт       {chain['report']}",
    ]
    return "\n".join(lines)

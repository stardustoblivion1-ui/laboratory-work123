"""Отчёт JSON о несоответствиях и история проверок."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def write_report(baseline: dict, drift: dict, out: str | Path,
                 history: str | Path | None = None) -> dict:
    nonconf = ([{"path": p, "kind": k} for k in ("added", "removed", "modified") for p in drift[k]])
    rep = {
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "baseline": baseline["id"],
        "baseline_commit": baseline.get("commit_hash"),
        "compliant": not nonconf,
        "summary": {k: len(drift[k]) for k in ("added", "removed", "modified")},
        "nonconformities": nonconf,
    }
    Path(out).write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    if history:
        with Path(history).open("a", encoding="utf-8") as f:
            f.write(json.dumps({k: rep[k] for k in ("checked_at", "baseline", "compliant", "summary")},
                               ensure_ascii=False) + "\n")
    return rep

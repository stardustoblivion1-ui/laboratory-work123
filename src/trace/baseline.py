"""Неизменяемые baseline и проверка файлов по baseline."""
from __future__ import annotations

import subprocess
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS baselines (
    id TEXT PRIMARY KEY, created_at TEXT NOT NULL, git_commit TEXT);
CREATE TABLE IF NOT EXISTS baseline_items (
    baseline_id TEXT NOT NULL REFERENCES baselines(id), ci_id TEXT NOT NULL, path TEXT NOT NULL,
    version TEXT NOT NULL, sha256 TEXT NOT NULL, PRIMARY KEY (baseline_id, ci_id));
CREATE TRIGGER IF NOT EXISTS bl_no_update BEFORE UPDATE ON baselines
BEGIN SELECT RAISE(ABORT, 'baseline is immutable'); END;
CREATE TRIGGER IF NOT EXISTS bl_no_delete BEFORE DELETE ON baselines
BEGIN SELECT RAISE(ABORT, 'baseline is immutable'); END;
CREATE TRIGGER IF NOT EXISTS bli_no_update BEFORE UPDATE ON baseline_items
BEGIN SELECT RAISE(ABORT, 'baseline is immutable'); END;
CREATE TRIGGER IF NOT EXISTS bli_no_delete BEFORE DELETE ON baseline_items
BEGIN SELECT RAISE(ABORT, 'baseline is immutable'); END;
"""


def git_head(root: str | Path) -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                           capture_output=True, text=True, check=False)
    except OSError:
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def create_baseline(reg, root: str | Path, commit_hash: str | None = None) -> str:
    from .registry import TraceError, _now
    items = reg.list_ci()
    if not items:
        raise TraceError("Нельзя создать baseline: нет зарегистрированных КЕ")
    bid = reg._next("baselines", "BL")
    reg.conn.execute("INSERT INTO baselines (id, created_at, git_commit) VALUES (?,?,?)",
                     (bid, _now(), commit_hash or git_head(root)))
    reg.conn.executemany(
        "INSERT INTO baseline_items (baseline_id, ci_id, path, version, sha256) VALUES (?,?,?,?,?)",
        [(bid, i["id"], i["path"], i["version"], i["sha256"]) for i in items])
    # применённые запросы без baseline привязываются к ней
    reg.conn.execute("UPDATE change_requests SET baseline_id=? "
                     "WHERE status='applied' AND baseline_id IS NULL", (bid,))
    reg.conn.commit()
    return bid


def get_baseline(reg, baseline_id: str) -> dict:
    from .registry import TraceError
    row = reg.conn.execute("SELECT * FROM baselines WHERE id=?", (baseline_id,)).fetchone()
    if row is None:
        raise TraceError(f"Baseline {baseline_id} не найдена")
    items = [dict(r) for r in reg.conn.execute(
        "SELECT ci_id, path, version, sha256 FROM baseline_items WHERE baseline_id=? ORDER BY ci_id",
        (baseline_id,))]
    return {**dict(row), "items": items}


def verify_baseline(reg, baseline_id: str, root: str | Path) -> dict:
    from .registry import sha256_of
    bl = get_baseline(reg, baseline_id)
    modified, missing = [], []
    for it in bl["items"]:
        f = Path(root) / it["path"]
        if not f.is_file():
            missing.append(it["path"])
        elif sha256_of(f) != it["sha256"]:
            modified.append(it["path"])
    return {"baseline": baseline_id, "ok": not (modified or missing),
            "modified": modified, "missing": missing}

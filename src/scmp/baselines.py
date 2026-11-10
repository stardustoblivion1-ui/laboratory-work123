"""Неизменяемые baseline: набор «CI → версия»; сравнение двух baseline."""
from __future__ import annotations

import sqlite3

from .common import ScmError, log, now, require_text
from .registry import list_cis, project_id

SCHEMA = """
CREATE TABLE IF NOT EXISTS baselines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    name TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE (project_id, name));
CREATE TABLE IF NOT EXISTS baseline_items (
    baseline_id INTEGER NOT NULL REFERENCES baselines(id),
    ci_name TEXT NOT NULL, version TEXT NOT NULL, PRIMARY KEY (baseline_id, ci_name));
CREATE TRIGGER IF NOT EXISTS baselines_no_update BEFORE UPDATE ON baselines
BEGIN SELECT RAISE(ABORT, 'baseline is immutable'); END;
CREATE TRIGGER IF NOT EXISTS baselines_no_delete BEFORE DELETE ON baselines
BEGIN SELECT RAISE(ABORT, 'baseline is immutable'); END;
CREATE TRIGGER IF NOT EXISTS items_no_update BEFORE UPDATE ON baseline_items
BEGIN SELECT RAISE(ABORT, 'baseline is immutable'); END;
CREATE TRIGGER IF NOT EXISTS items_no_delete BEFORE DELETE ON baseline_items
BEGIN SELECT RAISE(ABORT, 'baseline is immutable'); END;
"""


def create_baseline(conn, project: str, name: str) -> int:
    name = require_text(name, "Имя baseline")
    pid = project_id(conn, project)
    items = list_cis(conn, project)
    if not items:
        raise ScmError("Нельзя создать baseline: в проекте нет конфигурационных единиц")
    try:
        cur = conn.execute("INSERT INTO baselines (project_id, name, created_at) VALUES (?,?,?)",
                           (pid, name, now()))
    except sqlite3.IntegrityError:
        raise ScmError(f"Baseline «{name}» уже существует и не может быть изменена") from None
    conn.executemany("INSERT INTO baseline_items (baseline_id, ci_name, version) VALUES (?,?,?)",
                     [(cur.lastrowid, i["name"], i["version"]) for i in items])
    log(conn, pid, "baseline.create", f"{name} ({len(items)} CI)")
    conn.commit()
    return cur.lastrowid


def get_baseline(conn, project: str, name: str) -> dict:
    pid = project_id(conn, project)
    row = conn.execute("SELECT * FROM baselines WHERE project_id=? AND name=?", (pid, name)).fetchone()
    if row is None:
        raise ScmError(f"Baseline «{name}» не найдена в проекте «{project}»")
    items = conn.execute("SELECT ci_name, version FROM baseline_items WHERE baseline_id=?", (row["id"],))
    return {"id": row["id"], "name": name, "created_at": row["created_at"],
            "items": {r["ci_name"]: r["version"] for r in items}}


def list_baselines(conn, project: str) -> list[str]:
    pid = project_id(conn, project)
    return [r["name"] for r in conn.execute(
        "SELECT name FROM baselines WHERE project_id=? ORDER BY id", (pid,))]


def compare(conn, project: str, a: str, b: str) -> dict:
    ia, ib = get_baseline(conn, project, a)["items"], get_baseline(conn, project, b)["items"]
    return {
        "added": sorted(set(ib) - set(ia)),
        "removed": sorted(set(ia) - set(ib)),
        "changed": {k: {"from": ia[k], "to": ib[k]} for k in sorted(set(ia) & set(ib)) if ia[k] != ib[k]},
    }

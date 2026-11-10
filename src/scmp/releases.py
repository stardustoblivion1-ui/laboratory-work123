"""Регистрация релизов, история и отчёты."""
from __future__ import annotations

import sqlite3

from .baselines import get_baseline, list_baselines
from .changes import list_changes
from .common import ScmError, log, now, parse_semver
from .registry import list_cis, project_id

SCHEMA = """
CREATE TABLE IF NOT EXISTS releases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    version TEXT NOT NULL, baseline_id INTEGER NOT NULL REFERENCES baselines(id),
    created_at TEXT NOT NULL, UNIQUE (project_id, version));
"""


def register_release(conn, project: str, version: str, baseline: str) -> int:
    v = parse_semver(version)
    pid = project_id(conn, project)
    bl = get_baseline(conn, project, baseline)
    last = conn.execute("SELECT version FROM releases WHERE project_id=?", (pid,)).fetchall()
    if last and v <= max(parse_semver(r["version"]) for r in last):
        raise ScmError(f"Версия релиза {version} должна быть больше всех предыдущих")
    try:
        cur = conn.execute("INSERT INTO releases (project_id, version, baseline_id, created_at) "
                           "VALUES (?,?,?,?)", (pid, version, bl["id"], now()))
    except sqlite3.IntegrityError:
        raise ScmError(f"Релиз {version} уже зарегистрирован") from None
    log(conn, pid, "release.register", f"{version} on {baseline}")
    conn.commit()
    return cur.lastrowid


def list_releases(conn, project: str) -> list[dict]:
    pid = project_id(conn, project)
    rows = conn.execute("SELECT r.version, b.name AS baseline, r.created_at FROM releases r "
                        "JOIN baselines b ON b.id=r.baseline_id WHERE r.project_id=? ORDER BY r.id", (pid,))
    return [dict(r) for r in rows]


def history(conn, project: str) -> list[dict]:
    pid = project_id(conn, project)
    rows = conn.execute("SELECT time, action, details FROM history WHERE project_id=? ORDER BY id", (pid,))
    return [dict(r) for r in rows]


def report(conn, project: str) -> dict:
    changes = list_changes(conn, project)
    by_status: dict[str, int] = {}
    for c in changes:
        by_status[c["status"]] = by_status.get(c["status"], 0) + 1
    return {
        "project": project,
        "configuration_items": list_cis(conn, project),
        "changes": {"total": len(changes), "by_status": by_status},
        "baselines": {n: get_baseline(conn, project, n)["items"] for n in list_baselines(conn, project)},
        "releases": list_releases(conn, project),
        "history_events": len(history(conn, project)),
    }

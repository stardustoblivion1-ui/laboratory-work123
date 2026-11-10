"""Запросы на изменение: создание, решение об одобрении, применение."""
from __future__ import annotations

from .common import ScmError, log, now, parse_semver, require_text
from .registry import ci_id, current_version, project_id

STATUSES = ("proposed", "approved", "rejected", "applied")

SCHEMA = """
CREATE TABLE IF NOT EXISTS change_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'proposed',
    created_at TEXT NOT NULL,
    decided_by TEXT, decision_note TEXT, decided_at TEXT);
"""


def _get(conn, change_id: int):
    row = conn.execute("SELECT * FROM change_requests WHERE id=?", (change_id,)).fetchone()
    if row is None:
        raise ScmError(f"Запрос на изменение {change_id} не найден")
    return row


def create_change(conn, project: str, title: str, description: str = "") -> int:
    title = require_text(title, "Заголовок запроса")
    pid = project_id(conn, project)
    cur = conn.execute(
        "INSERT INTO change_requests (project_id, title, description, created_at) VALUES (?,?,?,?)",
        (pid, title, description, now()))
    log(conn, pid, "change.create", f"#{cur.lastrowid} {title}")
    conn.commit()
    return cur.lastrowid


def decide(conn, change_id: int, approve: bool, by: str, note: str = "") -> str:
    by = require_text(by, "Лицо, принимающее решение,")
    ch = _get(conn, change_id)
    if ch["status"] != "proposed":
        raise ScmError(f"Решение по запросу {change_id} уже принято (статус {ch['status']})")
    status = "approved" if approve else "rejected"
    conn.execute("UPDATE change_requests SET status=?, decided_by=?, decision_note=?, decided_at=? "
                 "WHERE id=?", (status, by, note, now(), change_id))
    log(conn, ch["project_id"], f"change.{status}", f"#{change_id} by {by}")
    conn.commit()
    return status


def apply_change(conn, change_id: int, ci_name: str, new_version: str, content_hash: str) -> None:
    """Создаёт новую версию CI. Допустимо только для одобренного запроса."""
    ch = _get(conn, change_id)
    if ch["status"] != "approved":
        raise ScmError(
            f"Запрос {change_id} нельзя применить: статус «{ch['status']}», требуется «approved»")
    parse_semver(new_version)
    project = conn.execute("SELECT name FROM projects WHERE id=?", (ch["project_id"],)).fetchone()
    cid = ci_id(conn, project["name"], ci_name)
    if parse_semver(new_version) <= parse_semver(current_version(conn, cid)):
        raise ScmError(
            f"Новая версия {new_version} должна быть больше текущей {current_version(conn, cid)}")
    conn.execute("INSERT INTO ci_versions (ci_id, version, content_hash, created_at, change_id) "
                 "VALUES (?,?,?,?,?)", (cid, new_version, content_hash, now(), change_id))
    conn.execute("UPDATE change_requests SET status='applied' WHERE id=?", (change_id,))
    log(conn, ch["project_id"], "change.apply", f"#{change_id} {ci_name}@{new_version}")
    conn.commit()


def list_changes(conn, project: str, status: str | None = None) -> list[dict]:
    pid = project_id(conn, project)
    rows = conn.execute("SELECT * FROM change_requests WHERE project_id=? ORDER BY id", (pid,))
    return [dict(r) for r in rows if status is None or r["status"] == status]

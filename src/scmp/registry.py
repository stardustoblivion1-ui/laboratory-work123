"""Регистрация проектов, конфигурационных единиц и их версий."""
from __future__ import annotations

import sqlite3

from .common import ScmError, log, now, parse_semver, require_text


def project_id(conn, name: str) -> int:
    row = conn.execute("SELECT id FROM projects WHERE name=?", (name,)).fetchone()
    if row is None:
        raise ScmError(f"Проект «{name}» не найден")
    return row["id"]


def register_project(conn, name: str) -> int:
    name = require_text(name, "Название проекта")
    try:
        cur = conn.execute("INSERT INTO projects (name, created_at) VALUES (?,?)", (name, now()))
    except sqlite3.IntegrityError:
        raise ScmError(f"Проект «{name}» уже зарегистрирован") from None
    log(conn, cur.lastrowid, "project.register", name)
    conn.commit()
    return cur.lastrowid


def ci_id(conn, project: str, name: str) -> int:
    row = conn.execute("SELECT id FROM cis WHERE project_id=? AND name=?",
                       (project_id(conn, project), name)).fetchone()
    if row is None:
        raise ScmError(f"Конфигурационная единица «{project}/{name}» не найдена")
    return row["id"]


def register_ci(conn, project: str, name: str, version: str = "1.0.0",
                content_hash: str = "initial") -> int:
    """Первичная регистрация CI вместе с начальной версией (запрос не требуется)."""
    name = require_text(name, "Название CI")
    parse_semver(version)
    pid = project_id(conn, project)
    try:
        cur = conn.execute("INSERT INTO cis (project_id, name) VALUES (?,?)", (pid, name))
    except sqlite3.IntegrityError:
        raise ScmError(f"CI «{project}/{name}» уже зарегистрирована") from None
    conn.execute(
        "INSERT INTO ci_versions (ci_id, version, content_hash, created_at) VALUES (?,?,?,?)",
        (cur.lastrowid, version, content_hash, now()))
    log(conn, pid, "ci.register", f"{name}@{version}")
    conn.commit()
    return cur.lastrowid


def current_version(conn, cid: int) -> str:
    row = conn.execute("SELECT version FROM ci_versions WHERE ci_id=? ORDER BY id DESC LIMIT 1",
                       (cid,)).fetchone()
    return row["version"]


def list_cis(conn, project: str) -> list[dict]:
    pid = project_id(conn, project)
    rows = conn.execute("SELECT id, name FROM cis WHERE project_id=? ORDER BY name", (pid,))
    return [{"name": r["name"], "version": current_version(conn, r["id"])} for r in rows]


def list_projects(conn) -> list[str]:
    return [r["name"] for r in conn.execute("SELECT name FROM projects ORDER BY name")]

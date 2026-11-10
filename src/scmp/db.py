"""Подключение к SQLite и применение схем модулей."""
from __future__ import annotations

import sqlite3

CORE_SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS cis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    name TEXT NOT NULL, UNIQUE (project_id, name));
CREATE TABLE IF NOT EXISTS ci_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ci_id INTEGER NOT NULL REFERENCES cis(id),
    version TEXT NOT NULL, content_hash TEXT NOT NULL, created_at TEXT NOT NULL,
    change_id INTEGER, UNIQUE (ci_id, version));
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT NOT NULL,
    project_id INTEGER, action TEXT NOT NULL, details TEXT NOT NULL DEFAULT '');
"""


def connect(path: str = "scmp.db") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(CORE_SCHEMA)
    conn.commit()
    return conn

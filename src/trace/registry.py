"""SQLite-реестр: конфигурационные единицы, запросы на изменение, решения."""
from __future__ import annotations

import hashlib
import re
import sqlite3
from datetime import datetime
from pathlib import Path

SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")

SCHEMA = """
CREATE TABLE IF NOT EXISTS ci (
    id TEXT PRIMARY KEY, path TEXT NOT NULL UNIQUE, version TEXT NOT NULL, sha256 TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS change_requests (
    id TEXT PRIMARY KEY, ci_id TEXT NOT NULL REFERENCES ci(id), title TEXT NOT NULL,
    new_version TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'proposed', created_at TEXT NOT NULL,
    commit_hash TEXT, baseline_id TEXT, test_ref TEXT);
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT, cr_id TEXT NOT NULL REFERENCES change_requests(id),
    approved INTEGER NOT NULL, decided_by TEXT NOT NULL, note TEXT NOT NULL DEFAULT '',
    decided_at TEXT NOT NULL);
"""


class TraceError(Exception):
    """Ошибка реестра/процесса управления конфигурацией."""


def semver(v: str) -> tuple[int, int, int]:
    m = SEMVER.match(v) if isinstance(v, str) else None
    if not m:
        raise TraceError(f"Некорректная версия {v!r}: ожидается MAJOR.MINOR.PATCH")
    return tuple(int(x) for x in m.groups())


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class Registry:
    def __init__(self, db: str = "trace.db"):
        self.conn = sqlite3.connect(db)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        from . import baseline
        self.conn.executescript(baseline.SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def _next(self, table: str, prefix: str) -> str:
        n = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        return f"{prefix}-{n + 1:03d}"

    # --- КЕ ---
    def register_ci(self, root: str | Path, path: str, version: str = "1.0.0") -> str:
        semver(version)
        f = Path(root) / path
        if not f.is_file():
            raise TraceError(f"Файл не найден: {path}")
        if self.conn.execute("SELECT 1 FROM ci WHERE path=?", (path,)).fetchone():
            raise TraceError(f"КЕ с путём {path} уже зарегистрирована")
        cid = self._next("ci", "CI")
        self.conn.execute("INSERT INTO ci (id, path, version, sha256) VALUES (?,?,?,?)",
                          (cid, path, version, sha256_of(f)))
        self.conn.commit()
        return cid

    def get_ci(self, ci_id: str) -> dict:
        row = self.conn.execute("SELECT * FROM ci WHERE id=?", (ci_id,)).fetchone()
        if row is None:
            raise TraceError(f"КЕ {ci_id} не найдена")
        return dict(row)

    def list_ci(self) -> list[dict]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM ci ORDER BY id")]

    # --- запросы и решения ---
    def create_request(self, ci_id: str, title: str, new_version: str) -> str:
        ci = self.get_ci(ci_id)
        if not title.strip():
            raise TraceError("Заголовок запроса не может быть пустым")
        if semver(new_version) <= semver(ci["version"]):
            raise TraceError(f"Новая версия {new_version} должна быть больше текущей {ci['version']}")
        crid = self._next("change_requests", "CR")
        self.conn.execute(
            "INSERT INTO change_requests (id, ci_id, title, new_version, created_at) VALUES (?,?,?,?,?)",
            (crid, ci_id, title.strip(), new_version, _now()))
        self.conn.commit()
        return crid

    def get_request(self, cr_id: str) -> dict:
        row = self.conn.execute("SELECT * FROM change_requests WHERE id=?", (cr_id,)).fetchone()
        if row is None:
            raise TraceError(f"Запрос {cr_id} не найден")
        return dict(row)

    def list_requests(self) -> list[dict]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM change_requests ORDER BY id")]

    def decide(self, cr_id: str, approve: bool, by: str, note: str = "") -> str:
        if not by.strip():
            raise TraceError("Не указано лицо, принимающее решение")
        cr = self.get_request(cr_id)
        if cr["status"] != "proposed":
            raise TraceError(f"Решение по {cr_id} уже принято (статус {cr['status']})")
        status = "approved" if approve else "rejected"
        self.conn.execute("UPDATE change_requests SET status=? WHERE id=?", (status, cr_id))
        self.conn.execute(
            "INSERT INTO decisions (cr_id, approved, decided_by, note, decided_at) VALUES (?,?,?,?,?)",
            (cr_id, int(approve), by.strip(), note, _now()))
        self.conn.commit()
        return status

    def get_decision(self, cr_id: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM decisions WHERE cr_id=? ORDER BY id DESC LIMIT 1",
                                (cr_id,)).fetchone()
        return dict(row) if row else None

    def apply(self, cr_id: str, root: str | Path) -> None:
        """Фиксирует в реестре новую версию и SHA-256 КЕ. Только для одобренного запроса."""
        cr = self.get_request(cr_id)
        if cr["status"] != "approved":
            raise TraceError(f"Запрос {cr_id} нельзя применить: статус «{cr['status']}», нужен «approved»")
        ci = self.get_ci(cr["ci_id"])
        f = Path(root) / ci["path"]
        if not f.is_file():
            raise TraceError(f"Файл не найден: {ci['path']}")
        self.conn.execute("UPDATE ci SET version=?, sha256=? WHERE id=?",
                          (cr["new_version"], sha256_of(f), ci["id"]))
        self.conn.execute("UPDATE change_requests SET status='applied' WHERE id=?", (cr_id,))
        self.conn.commit()

    def link(self, cr_id: str, commit_hash: str | None = None, test_ref: str | None = None,
             baseline_id: str | None = None) -> dict:
        self.get_request(cr_id)
        if commit_hash is not None:
            h = commit_hash.strip().lower()
            if not (7 <= len(h) <= 40) or not re.fullmatch(r"[0-9a-f]+", h):
                raise TraceError("commit_hash должен быть hex-строкой длиной 7–40 символов")
            self.conn.execute("UPDATE change_requests SET commit_hash=? WHERE id=?", (h, cr_id))
        if test_ref is not None:
            self.conn.execute("UPDATE change_requests SET test_ref=? WHERE id=?", (test_ref, cr_id))
        if baseline_id is not None:
            self.conn.execute("UPDATE change_requests SET baseline_id=? WHERE id=?",
                              (baseline_id, cr_id))
        self.conn.commit()
        return self.get_request(cr_id)

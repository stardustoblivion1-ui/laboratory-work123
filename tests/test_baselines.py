import sqlite3

import pytest

from scmp import baselines, changes, registry
from scmp.common import ScmError


@pytest.fixture
def proj(conn):
    registry.register_project(conn, "shop")
    registry.register_ci(conn, "shop", "api")
    registry.register_ci(conn, "shop", "db")
    return conn


def bump(conn, ci, version):
    cid = changes.create_change(conn, "shop", f"{ci}->{version}")
    changes.decide(conn, cid, True, "Иванов")
    changes.apply_change(conn, cid, ci, version, "h")


def test_baseline_captures_current_versions(proj):
    baselines.create_baseline(proj, "shop", "BL-1")
    assert baselines.get_baseline(proj, "shop", "BL-1")["items"] == {"api": "1.0.0", "db": "1.0.0"}


def test_baseline_not_affected_by_later_changes(proj):
    baselines.create_baseline(proj, "shop", "BL-1")
    bump(proj, "api", "1.1.0")
    assert baselines.get_baseline(proj, "shop", "BL-1")["items"]["api"] == "1.0.0"


def test_baseline_is_immutable_in_database(proj):
    baselines.create_baseline(proj, "shop", "BL-1")
    for sql in ("UPDATE baselines SET name='x'", "DELETE FROM baselines",
                "UPDATE baseline_items SET version='9.9.9'", "DELETE FROM baseline_items"):
        with pytest.raises(sqlite3.DatabaseError, match="immutable"):
            proj.execute(sql)


def test_duplicate_baseline_name_rejected(proj):
    baselines.create_baseline(proj, "shop", "BL-1")
    with pytest.raises(ScmError, match="не может быть изменена"):
        baselines.create_baseline(proj, "shop", "BL-1")


def test_compare_two_baselines(proj):
    baselines.create_baseline(proj, "shop", "BL-1")
    bump(proj, "api", "1.1.0")
    registry.register_ci(proj, "shop", "web")
    baselines.create_baseline(proj, "shop", "BL-2")
    assert baselines.compare(proj, "shop", "BL-1", "BL-2") == {
        "added": ["web"], "removed": [], "changed": {"api": {"from": "1.0.0", "to": "1.1.0"}}}


def test_empty_project_and_unknown_baseline(conn):
    registry.register_project(conn, "empty")
    with pytest.raises(ScmError, match="нет конфигурационных"):
        baselines.create_baseline(conn, "empty", "BL-1")
    with pytest.raises(ScmError, match="не найдена"):
        baselines.get_baseline(conn, "empty", "nope")

import sqlite3

import pytest

from scmtrace import baseline
from scmtrace.registry import TraceError


def test_register_ci_records_path_version_sha(reg, root):
    cid = reg.register_ci(root, "app.py")
    ci = reg.get_ci(cid)
    assert ci["path"] == "app.py" and ci["version"] == "1.0.0" and len(ci["sha256"]) == 64


def test_register_ci_errors(reg, root):
    reg.register_ci(root, "app.py")
    with pytest.raises(TraceError, match="уже"):
        reg.register_ci(root, "app.py")
    with pytest.raises(TraceError, match="не найден"):
        reg.register_ci(root, "ghost.py")
    with pytest.raises(TraceError, match="MAJOR"):
        reg.register_ci(root, "lib.py", "1.0")


def test_change_version_through_approved_request(reg, root):
    cid = reg.register_ci(root, "app.py")
    cr = reg.create_request(cid, "Изменить вывод", "1.1.0")
    reg.decide(cr, True, "Иванов", "ок")
    (root / "app.py").write_text("print('v2')\n")
    reg.apply(cr, root)
    ci = reg.get_ci(cid)
    assert ci["version"] == "1.1.0" and reg.get_request(cr)["status"] == "applied"


def test_apply_updates_version_and_hash(reg, root):
    cid = reg.register_ci(root, "app.py")
    old = reg.get_ci(cid)["sha256"]
    cr = reg.create_request(cid, "x", "1.0.1")
    reg.decide(cr, True, "Иванов")
    (root / "app.py").write_text("changed\n")
    reg.apply(cr, root)
    assert reg.get_ci(cid)["sha256"] != old


def test_approve_and_reject(reg, root):
    cid = reg.register_ci(root, "app.py")
    a, b = reg.create_request(cid, "a", "1.1.0"), reg.create_request(cid, "b", "1.2.0")
    assert reg.decide(a, True, "Иванов") == "approved"
    assert reg.decide(b, False, "Иванов", "не нужно") == "rejected"
    assert reg.get_decision(b)["approved"] == 0
    with pytest.raises(TraceError, match="уже принято"):
        reg.decide(a, False, "Петров")


def test_unapproved_change_forbidden(reg, root):
    cid = reg.register_ci(root, "app.py")
    cr = reg.create_request(cid, "x", "1.1.0")
    with pytest.raises(TraceError, match="нельзя применить"):
        reg.apply(cr, root)
    reg.decide(cr, False, "Иванов")
    with pytest.raises(TraceError, match="нельзя применить"):
        reg.apply(cr, root)
    assert reg.get_ci(cid)["version"] == "1.0.0"


def test_request_validation(reg, root):
    cid = reg.register_ci(root, "app.py")
    with pytest.raises(TraceError, match="больше текущей"):
        reg.create_request(cid, "x", "1.0.0")
    with pytest.raises(TraceError):
        reg.create_request(cid, " ", "1.1.0")
    with pytest.raises(TraceError, match="не найдена"):
        reg.create_request("CI-999", "x", "1.1.0")


def test_baseline_create_and_verify_detects_changes(reg, root):
    reg.register_ci(root, "app.py")
    reg.register_ci(root, "lib.py")
    bid = baseline.create_baseline(reg, root, commit_hash="abc1234")
    assert baseline.verify_baseline(reg, bid, root)["ok"]
    (root / "lib.py").write_text("X = 2\n")
    (root / "app.py").unlink()
    res = baseline.verify_baseline(reg, bid, root)
    assert not res["ok"] and res["modified"] == ["lib.py"] and res["missing"] == ["app.py"]


def test_baseline_immutable(reg, root):
    reg.register_ci(root, "app.py")
    bid = baseline.create_baseline(reg, root)
    for sql in ("UPDATE baselines SET created_at='x'", "DELETE FROM baselines",
                "UPDATE baseline_items SET sha256='0'", "DELETE FROM baseline_items"):
        with pytest.raises(sqlite3.DatabaseError, match="immutable"):
            reg.conn.execute(sql)
    assert baseline.get_baseline(reg, bid)["items"][0]["path"] == "app.py"


def test_baseline_requires_ci_and_exists(reg, root):
    with pytest.raises(TraceError, match="нет зарегистрированных"):
        baseline.create_baseline(reg, root)
    with pytest.raises(TraceError, match="не найдена"):
        baseline.get_baseline(reg, "BL-999")

import pytest

from scmp import changes, registry
from scmp.common import ScmError


@pytest.fixture
def proj(conn):
    registry.register_project(conn, "shop")
    registry.register_ci(conn, "shop", "api")
    return conn


def test_approve_and_apply_creates_new_version(proj):
    cid = changes.create_change(proj, "shop", "Новый эндпоинт")
    assert changes.decide(proj, cid, True, "Иванов", "ок") == "approved"
    changes.apply_change(proj, cid, "api", "1.1.0", "h1")
    assert registry.list_cis(proj, "shop") == [{"name": "api", "version": "1.1.0"}]
    assert changes.list_changes(proj, "shop")[0]["status"] == "applied"


def test_unapproved_change_cannot_be_applied(proj):
    cid = changes.create_change(proj, "shop", "x")
    with pytest.raises(ScmError, match="нельзя применить"):
        changes.apply_change(proj, cid, "api", "1.1.0", "h")
    assert registry.list_cis(proj, "shop")[0]["version"] == "1.0.0"


def test_rejected_change_cannot_be_applied(proj):
    cid = changes.create_change(proj, "shop", "x")
    changes.decide(proj, cid, False, "Иванов", "нет")
    with pytest.raises(ScmError, match="rejected"):
        changes.apply_change(proj, cid, "api", "1.1.0", "h")


def test_decision_only_once_and_requires_person(proj):
    cid = changes.create_change(proj, "shop", "x")
    with pytest.raises(ScmError):
        changes.decide(proj, cid, True, " ")
    changes.decide(proj, cid, True, "Иванов")
    with pytest.raises(ScmError, match="уже принято"):
        changes.decide(proj, cid, False, "Петров")


def test_applied_change_cannot_be_reused(proj):
    cid = changes.create_change(proj, "shop", "x")
    changes.decide(proj, cid, True, "Иванов")
    changes.apply_change(proj, cid, "api", "1.1.0", "h")
    with pytest.raises(ScmError):
        changes.apply_change(proj, cid, "api", "1.2.0", "h")


def test_version_must_increase(proj):
    cid = changes.create_change(proj, "shop", "x")
    changes.decide(proj, cid, True, "Иванов")
    with pytest.raises(ScmError, match="больше текущей"):
        changes.apply_change(proj, cid, "api", "1.0.0", "h")


def test_unknown_change(proj):
    with pytest.raises(ScmError, match="не найден"):
        changes.decide(proj, 99, True, "Иванов")

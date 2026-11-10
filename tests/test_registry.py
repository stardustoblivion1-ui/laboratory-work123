import pytest

from scmp import registry
from scmp.common import ScmError


def test_register_project_and_duplicates(conn):
    registry.register_project(conn, "shop")
    with pytest.raises(ScmError, match="уже"):
        registry.register_project(conn, "shop")
    with pytest.raises(ScmError):
        registry.register_project(conn, "  ")


def test_register_ci_with_initial_version(conn):
    registry.register_project(conn, "shop")
    registry.register_ci(conn, "shop", "api")
    assert registry.list_cis(conn, "shop") == [{"name": "api", "version": "1.0.0"}]


def test_ci_validation(conn):
    registry.register_project(conn, "shop")
    registry.register_ci(conn, "shop", "api")
    with pytest.raises(ScmError):
        registry.register_ci(conn, "shop", "api")
    with pytest.raises(ScmError, match="MAJOR"):
        registry.register_ci(conn, "shop", "db", version="1.0")
    with pytest.raises(ScmError, match="не найден"):
        registry.register_ci(conn, "ghost", "x")


def test_same_ci_name_in_different_projects(conn):
    for p in ("a", "b"):
        registry.register_project(conn, p)
        registry.register_ci(conn, p, "core")
    assert registry.list_projects(conn) == ["a", "b"]

import pytest

from scmp import baselines, changes, registry, releases
from scmp.cli import run
from scmp.common import ScmError


def test_full_scenario_request_to_release(conn):
    """запрос → одобрение → изменение → baseline → релиз"""
    registry.register_project(conn, "shop")
    registry.register_ci(conn, "shop", "api")
    baselines.create_baseline(conn, "shop", "BL-1")
    cid = changes.create_change(conn, "shop", "Эндпоинт /orders")
    changes.decide(conn, cid, True, "Иванов", "согласовано")
    changes.apply_change(conn, cid, "api", "1.1.0", "sha-1")
    baselines.create_baseline(conn, "shop", "BL-2")
    releases.register_release(conn, "shop", "1.1.0", "BL-2")
    rep = releases.report(conn, "shop")
    assert rep["releases"][0]["baseline"] == "BL-2"
    assert rep["changes"]["by_status"] == {"applied": 1}
    assert rep["baselines"]["BL-2"] == {"api": "1.1.0"}
    actions = [h["action"] for h in releases.history(conn, "shop")]
    assert actions == ["project.register", "ci.register", "baseline.create", "change.create",
                       "change.approved", "change.apply", "baseline.create", "release.register"]


@pytest.fixture
def ready(conn):
    registry.register_project(conn, "shop")
    registry.register_ci(conn, "shop", "api")
    baselines.create_baseline(conn, "shop", "BL-1")
    return conn


def test_release_duplicate_and_decrease_rejected(ready):
    releases.register_release(ready, "shop", "1.0.0", "BL-1")
    with pytest.raises(ScmError, match="больше"):
        releases.register_release(ready, "shop", "1.0.0", "BL-1")
    releases.register_release(ready, "shop", "2.0.0", "BL-1")
    with pytest.raises(ScmError, match="больше"):
        releases.register_release(ready, "shop", "1.5.0", "BL-1")


def test_release_needs_existing_baseline_and_valid_version(ready):
    with pytest.raises(ScmError, match="не найдена"):
        releases.register_release(ready, "shop", "1.0.0", "NOPE")
    with pytest.raises(ScmError, match="MAJOR"):
        releases.register_release(ready, "shop", "1.0", "BL-1")


def test_projects_are_isolated(ready):
    registry.register_project(ready, "blog")
    registry.register_ci(ready, "blog", "web")
    assert registry.list_cis(ready, "blog") == [{"name": "web", "version": "1.0.0"}]
    assert baselines.list_baselines(ready, "blog") == []


def test_cli_scenario_and_errors(tmp_path, capsys):
    db = ["--db", str(tmp_path / "c.db")]
    for args in (["project", "add", "shop"], ["ci", "add", "shop", "api"],
                 ["change", "create", "shop", "x"]):
        assert run([*db, *args]) == 0
    assert run([*db, "change", "apply", "1", "api", "1.1.0"]) == 1      # не одобрено
    assert "нельзя применить" in capsys.readouterr().err
    assert run([*db, "change", "decide", "1", "approve", "--by", "Иванов"]) == 0
    assert run([*db, "change", "apply", "1", "api", "1.1.0", "--hash", "abc"]) == 0
    assert run([*db, "baseline", "create", "shop", "BL-1"]) == 0
    assert run([*db, "release", "register", "shop", "1.1.0", "--baseline", "BL-1"]) == 0
    assert run([*db, "report", "shop"]) == 0
    assert '"version": "1.1.0"' in capsys.readouterr().out

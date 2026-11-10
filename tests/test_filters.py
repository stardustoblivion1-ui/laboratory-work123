import pytest

from taskman.cli import run
from taskman.db import TaskDB
from taskman.filters import filter_tasks


@pytest.fixture
def db(tmp_path):
    d = TaskDB(str(tmp_path / "t.db"))
    d.add("a", "Ivan", "high")
    d.add("b", "Ivan", "low")
    d.add("c", "Petr", "high")
    d.update(3, status="done")
    yield d
    d.close()


def test_filter_by_each_field(db):
    assert len(filter_tasks(db, assignee="Ivan")) == 2
    assert len(filter_tasks(db, priority="high")) == 2
    assert len(filter_tasks(db, status="done")) == 1


def test_filter_combined_and_empty(db):
    assert [t["title"] for t in filter_tasks(db, "Ivan", "high", "todo")] == ["a"]
    assert filter_tasks(db, assignee="Nobody") == []


def test_cli_filter(tmp_path, capsys):
    dbp = str(tmp_path / "c.db")
    run(["--db", dbp, "add", "x", "--assignee", "Ivan"])
    capsys.readouterr()
    assert run(["--db", dbp, "filter", "--assignee", "Ivan"]) == 0
    assert "x" in capsys.readouterr().out

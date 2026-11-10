import pytest

from taskman.db import TaskDB, TaskError


@pytest.fixture
def db(tmp_path):
    d = TaskDB(str(tmp_path / "t.db"))
    yield d
    d.close()


def test_add_and_get(db):
    i = db.add("Task", "Ivan", "high", "2026-12-01")
    t = db.get(i)
    assert t["status"] == "todo" and t["priority"] == "high" and t["assignee"] == "Ivan"


def test_update_and_delete(db):
    i = db.add("Task", "Ivan")
    assert db.update(i, status="done")["status"] == "done"
    db.delete(i)
    with pytest.raises(TaskError):
        db.get(i)


def test_validation_errors(db):
    with pytest.raises(TaskError):
        db.add("", "Ivan")
    with pytest.raises(TaskError):
        db.add("T", "Ivan", priority="urgent")
    with pytest.raises(TaskError):
        db.add("T", "Ivan", due="31.12.2026")
    i = db.add("T", "Ivan")
    with pytest.raises(TaskError):
        db.update(i, status="finished")
    with pytest.raises(TaskError):
        db.update(999, status="done")


def test_persistence_after_restart(tmp_path):
    p = str(tmp_path / "t.db")
    d1 = TaskDB(p)
    d1.add("Keep me", "Ivan")
    d1.close()
    d2 = TaskDB(p)
    assert [t["title"] for t in d2.all()] == ["Keep me"]
    d2.close()

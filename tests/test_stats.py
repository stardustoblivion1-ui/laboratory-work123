from taskman.cli import run
from taskman.db import TaskDB
from taskman.stats import statistics


def test_empty_statistics(tmp_path):
    d = TaskDB(str(tmp_path / "t.db"))
    assert statistics(d)["percent_done"] == 0.0
    d.close()


def test_statistics_counts(tmp_path):
    d = TaskDB(str(tmp_path / "t.db"))
    d.add("a", "Ivan")
    d.add("b", "Petr")
    d.update(1, status="done")
    st = statistics(d)
    assert st["total"] == 2 and st["done"] == 1 and st["percent_done"] == 50.0
    assert st["by_assignee"] == {"Ivan": 1, "Petr": 1}
    d.close()


def test_cli_stats(tmp_path, capsys):
    dbp = str(tmp_path / "c.db")
    run(["--db", dbp, "add", "x", "--assignee", "Ivan"])
    capsys.readouterr()
    assert run(["--db", dbp, "stats"]) == 0
    assert "Всего: 1" in capsys.readouterr().out

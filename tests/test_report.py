import json

from tracker.cli import run
from tracker.report import build_report, export_json
from tracker.store import ChangeTracker


def test_report_summary_and_traceability(tmp_path):
    tr = ChangeTracker(tmp_path / "c.json")
    a = tr.add("Ivan", "feature", "a")
    tr.add("Petr", "bugfix", "b")
    tr.link_commit(a.id, "abc1234")
    r = build_report(tr)
    assert r["total"] == 2 and r["by_status"] == {"planned": 2}
    assert r["traceable"] == [{"id": a.id, "commit_hash": "abc1234"}]
    assert r["without_commit"] == ["CH-002"]


def test_export_json_file_and_cli(tmp_path):
    db, out = tmp_path / "c.json", tmp_path / "r.json"
    assert run(["--db", str(db), "add", "--author", "Ivan", "--type", "docs", "--desc", "x"]) == 0
    assert run(["--db", str(db), "report", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["total"] == 1
    export_json(ChangeTracker(db), tmp_path / "r2.json")
    assert (tmp_path / "r2.json").exists()


def test_cli_reports_errors(tmp_path, capsys):
    db = str(tmp_path / "c.json")
    assert run(["--db", db, "status", "CH-999", "done"]) == 1
    assert "не найдено" in capsys.readouterr().err

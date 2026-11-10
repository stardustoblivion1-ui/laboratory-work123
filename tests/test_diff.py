import json
import os

import pytest

from cfgctl import baseline as bl
from cfgctl.cli import run
from cfgctl.diff import compare, has_drift
from cfgctl.scanner import scan


@pytest.fixture
def proj(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    (root / "a.txt").write_text("a")
    (root / "b.txt").write_text("b")
    return root


def test_no_drift(proj, tmp_path):
    data, _ = bl.create(proj, tmp_path / "bl", "Ivanov", commit_hash="abc")
    assert not has_drift(compare(data["items"], scan(proj)))


def test_modified_added_removed(proj, tmp_path):
    data, _ = bl.create(proj, tmp_path / "bl", "Ivanov")
    (proj / "a.txt").write_text("changed")
    (proj / "b.txt").unlink()
    (proj / "c.txt").write_text("new")
    d = compare(data["items"], scan(proj))
    assert d == {"added": ["c.txt"], "removed": ["b.txt"], "modified": ["a.txt"]}


def test_missing_baseline(tmp_path):
    with pytest.raises(bl.BaselineError):
        bl.load(tmp_path / "nope.json")


def test_baseline_is_readonly_and_ids_unique(proj, tmp_path):
    d1, p1 = bl.create(proj, tmp_path / "bl", "Ivanov")
    d2, _ = bl.create(proj, tmp_path / "bl", "Ivanov", previous_id=d1["id"])
    assert d1["id"] != d2["id"] and d2["previous"] == d1["id"]
    assert not os.access(p1, os.W_OK) or os.geteuid() == 0


def test_tampered_baseline_detected(proj, tmp_path):
    _, p = bl.create(proj, tmp_path / "bl", "Ivanov")
    os.chmod(p, 0o644)
    raw = json.loads(p.read_text())
    raw["items"]["a.txt"]["sha256"] = "0" * 64
    p.write_text(json.dumps(raw))
    with pytest.raises(bl.BaselineError):
        bl.load(p)


def test_unknown_previous_and_empty_approver(proj, tmp_path):
    with pytest.raises(bl.BaselineError):
        bl.create(proj, tmp_path / "bl", "Ivanov", previous_id="BL-0042")
    with pytest.raises(bl.BaselineError):
        bl.create(proj, tmp_path / "bl", " ")


def test_baseline_dir_not_scanned_when_inside_project(proj):
    bl.create(proj, proj / "baselines", "Ivanov")
    d, _ = bl.create(proj, proj / "baselines", "Ivanov")
    assert all(not p.startswith("baselines/") for p in d["items"])


def test_cli_check_report_and_exit_codes(proj, tmp_path):
    bdir = tmp_path / "bl"
    assert run(["baseline", str(proj), "--by", "Ivanov", "--dir", str(bdir)]) == 0
    args = ["check", str(proj), "--baseline", str(bdir / "BL-0001.json"),
            "--report", str(tmp_path / "r.json"), "--history", str(tmp_path / "h.jsonl")]
    assert run(args) == 0
    (proj / "a.txt").write_text("X")
    assert run(args) == 1
    rep = json.loads((tmp_path / "r.json").read_text())
    assert rep["nonconformities"] == [{"path": "a.txt", "kind": "modified"}]
    assert len((tmp_path / "h.jsonl").read_text().splitlines()) == 2
    assert run(["check", str(proj), "--baseline", str(tmp_path / "none.json")]) == 2

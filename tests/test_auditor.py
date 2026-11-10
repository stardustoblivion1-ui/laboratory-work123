import json
import subprocess

import pytest

from auditor.audit import run_audit, write_html, write_json
from auditor.cli import run
from auditor.rules import DEFAULT_RULES, load_rules


def git(root, *args):
    subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                   check=True, capture_output=True)


def make_project(root, commits=3, version="1.0.0", ci=True, files=True):
    root.mkdir(parents=True, exist_ok=True)
    if files:
        (root / "README.md").write_text("# x")
        (root / "CHANGELOG.md").write_text("# c")
    (root / "pyproject.toml").write_text(f'[project]\nname="x"\nversion="{version}"\n')
    if ci:
        (root / ".github/workflows").mkdir(parents=True)
        (root / ".github/workflows/ci.yml").write_text("name: ci\n")
    git(root, "init", "-q")
    for i in range(commits):
        (root / f"f{i}.txt").write_text(str(i))
        git(root, "add", "-A")
        git(root, "commit", "-qm", f"c{i}")
    return root


def failed(report, category):
    return [r for r in report["results"] if r["category"] == category and not r["passed"]]


def test_compliant_project(tmp_path):
    rep = run_audit(make_project(tmp_path / "p"))
    assert rep["compliant"] and not any(rep["summary"].values())


def test_missing_required_files(tmp_path):
    rep = run_audit(make_project(tmp_path / "p", files=False))
    assert {r["rule"] for r in failed(rep, "files")} == {"file:README.md", "file:CHANGELOG.md"}
    assert rep["summary"]["high"] == 1 and rep["summary"]["medium"] == 1


def test_not_a_git_repo_is_critical(tmp_path):
    root = tmp_path / "p"
    root.mkdir()
    rep = run_audit(root)
    assert any(r["rule"] == "git" and r["severity"] == "critical" for r in failed(rep, "git"))
    assert rep["summary"]["critical"] == 1


def test_too_few_commits(tmp_path):
    rep = run_audit(make_project(tmp_path / "p", commits=1))
    assert [r["rule"] for r in failed(rep, "git")] == ["min_commits"]


def test_missing_ci(tmp_path):
    rep = run_audit(make_project(tmp_path / "p", ci=False))
    assert len(failed(rep, "ci")) == 1


@pytest.mark.parametrize("bad", ["1.0", "v1.0.0", "1.0.0-beta", "latest"])
def test_bad_version_format(tmp_path, bad):
    rep = run_audit(make_project(tmp_path / "p", version=bad))
    assert len(failed(rep, "version")) == 1


def test_corrupted_pyproject_does_not_crash(tmp_path):
    root = make_project(tmp_path / "p")
    (root / "pyproject.toml").write_text("[[[ not toml")
    rep = run_audit(root)
    assert "повреждён" in failed(rep, "version")[0]["message"]


def test_missing_project_directory(tmp_path):
    rep = run_audit(tmp_path / "nope")
    assert not rep["compliant"] and rep["summary"]["critical"] == 1


def test_corrupted_rules_file_falls_back_to_defaults(tmp_path):
    rules = tmp_path / "rules.json"
    rules.write_text("{broken")
    loaded, warns = load_rules(rules)
    assert loaded == DEFAULT_RULES and "повреждён" in warns[0]
    rep = run_audit(make_project(tmp_path / "p"), rules)
    assert len(failed(rep, "config")) == 1


def test_missing_rules_file_warning(tmp_path):
    _, warns = load_rules(tmp_path / "none.json")
    assert "не найден" in warns[0]


def test_custom_rules_change_behaviour(tmp_path):
    rules = tmp_path / "r.json"
    rules.write_text(json.dumps({"min_commits": {"count": 10, "severity": "low"}}))
    rep = run_audit(make_project(tmp_path / "p"), rules)
    assert rep["summary"]["low"] == 1 and rep["compliant"] is False


def test_reports_json_and_html(tmp_path):
    rep = run_audit(make_project(tmp_path / "p", ci=False))
    write_json(rep, tmp_path / "r.json")
    write_html(rep, tmp_path / "r.html")
    assert json.loads((tmp_path / "r.json").read_text())["compliant"] is False
    page = (tmp_path / "r.html").read_text()
    assert "<table>" in page and "medium" in page and "не является сертификацией" in page


def test_cli_exit_codes(tmp_path):
    good, bad = make_project(tmp_path / "g"), make_project(tmp_path / "b", ci=False)
    out = ["--json", str(tmp_path / "o.json"), "--html", str(tmp_path / "o.html")]
    assert run(["audit", str(good), *out]) == 0
    assert run(["audit", str(bad), *out]) == 1

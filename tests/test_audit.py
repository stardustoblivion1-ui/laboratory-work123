import json
import subprocess

from scmtrace import baseline
from scmtrace.audit import audit, build_report, commit_exists, write_report


def git(root, *args):
    subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                   check=True, capture_output=True)


def head(root):
    return subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True,
                          text=True, check=True).stdout.strip()


def full_cycle(reg, root):
    """CR применён, закоммичен, включён в baseline и связан с тестом."""
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "init")
    cid = reg.register_ci(root, "app.py")
    cr = reg.create_request(cid, "Изменение", "1.1.0")
    reg.decide(cr, True, "Иванов")
    (root / "app.py").write_text("print('v2')\n")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "change app")
    reg.apply(cr, root)
    reg.link(cr, commit_hash=head(root), test_ref="tests/test_registry.py::test_apply_updates_version_and_hash")
    bid = baseline.create_baseline(reg, root)
    return cr, bid


def test_audit_passes_for_complete_chain(reg, root):
    full_cycle(reg, root)
    rep = build_report(reg, root)
    assert rep["compliant"] and rep["failed"] == []
    assert rep["requests_by_status"] == {"applied": 1}


def test_audit_detects_unapproved_file_change(reg, root):
    reg.register_ci(root, "app.py")
    (root / "app.py").write_text("tampered\n")
    failed = [f for f in audit(reg, root) if not f["ok"]]
    assert failed and failed[0]["check"] == "ci_file" and "без одобренного" in failed[0]["message"]


def test_audit_detects_unknown_commit_hash(reg, root):
    cr, _ = full_cycle(reg, root)
    reg.link(cr, commit_hash="deadbee")
    failed = [f for f in audit(reg, root) if not f["ok"]]
    assert [f["check"] for f in failed] == ["git_commit"]


def test_audit_requires_commit_baseline_and_test(reg, root):
    cid = reg.register_ci(root, "app.py")
    cr = reg.create_request(cid, "x", "1.1.0")
    reg.decide(cr, True, "Иванов")
    reg.apply(cr, root)
    checks = {f["check"] for f in audit(reg, root) if not f["ok"]}
    assert checks == {"git_commit", "baseline", "test"}


def test_report_json_written_with_baseline_checks(reg, root, tmp_path):
    full_cycle(reg, root)
    out = tmp_path / "audit.json"
    write_report(reg, root, out)
    data = json.loads(out.read_text())
    assert data["baseline_checks"][0]["ok"] is True and data["compliant"] is True


def test_commit_exists_helper(reg, root):
    full_cycle(reg, root)
    assert commit_exists(root, head(root))
    assert not commit_exists(root, "0123456789abcdef")

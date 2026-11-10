import subprocess
from pathlib import Path

import pytest

from scmtrace.chain import build_chain, render
from scmtrace.cli import run
from scmtrace.matrix import IMPLEMENTED, MISSING, PARTIAL, build_matrix, degree, render_markdown

PROJECT = Path(__file__).resolve().parents[1]


def test_matrix_references_are_all_real_except_unimplemented():
    rows = build_matrix(PROJECT)
    for r in rows:
        if r["status"] == MISSING:
            assert not r["function_ok"] and not r["test_ok"]
        else:
            assert r["function_ok"], r["function"]
            assert r["test_ok"], r["test"]


def test_matrix_markdown_and_degree():
    rows = build_matrix(PROJECT)
    md = render_markdown(rows)
    assert "SCMP-6" in md and "не реализован" in md
    d = degree(rows)
    assert d[IMPLEMENTED] + d[PARTIAL] + d[MISSING] == d["processes"] and 0 < d["score_percent"] < 100


def test_chain_for_full_cycle(reg, root):
    from tests.test_audit import full_cycle
    cr, bid = full_cycle(reg, root)
    ch = build_chain(reg, root, cr, "audit.json")
    assert ch["decision"]["approved"] and ch["commit"]["in_git_history"] and ch["baseline"] == bid
    text = render(ch)
    assert cr in text and "Иванов" in text and "audit.json" in text


def test_chain_without_links(reg, root):
    cid = reg.register_ci(root, "app.py")
    cr = reg.create_request(cid, "x", "1.1.0")
    text = render(build_chain(reg, root, cr))
    assert "— нет —" in text


def test_cli_full_flow_and_exit_codes(tmp_path, root, capsys):
    subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
    base = ["--db", str(tmp_path / "c.db"), "--root", str(root)]
    assert run([*base, "ci-add", "app.py"]) == 0
    assert run([*base, "request-create", "CI-001", "Правка", "1.1.0"]) == 0
    assert run([*base, "apply", "CR-001"]) == 2                       # не одобрено
    assert "нельзя применить" in capsys.readouterr().err
    assert run([*base, "decide", "CR-001", "approve", "--by", "Иванов"]) == 0
    (root / "app.py").write_text("new\n")
    assert run([*base, "apply", "CR-001"]) == 0
    assert run([*base, "baseline"]) == 0
    assert run([*base, "verify", "BL-001"]) == 0
    (root / "app.py").write_text("tampered\n")
    assert run([*base, "verify", "BL-001"]) == 1
    assert run([*base, "audit", "--report", str(tmp_path / "a.json")]) == 1


def test_cli_matrix_output_file(tmp_path, capsys):
    out = tmp_path / "m.md"
    assert run(["--db", str(tmp_path / "x.db"), "--root", str(PROJECT), "matrix", "--out", str(out)]) == 0
    assert "Матрица прослеживаемости" in out.read_text(encoding="utf-8")


@pytest.mark.parametrize("bad", [["decide", "CR-404", "approve", "--by", "x"], ["apply", "CR-404"]])
def test_cli_unknown_request(tmp_path, bad):
    assert run(["--db", str(tmp_path / "e.db"), *bad]) == 2

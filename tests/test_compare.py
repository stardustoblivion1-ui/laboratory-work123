from fvm.cli import run
from fvm.compare import diff_lines, has_changes
from fvm.storage import VersionStore


def test_diff_marks_added_and_removed():
    d = diff_lines("a\nb\nc\n", "a\nc\nd\n")
    assert "- b" in d and "+ d" in d and "  a" in d


def test_identical_texts_have_no_changes():
    assert not has_changes(diff_lines("x\n", "x\n"))


def test_cli_diff_between_two_real_states(tmp_path, capsys):
    doc = tmp_path / "f.txt"
    doc.write_text("one\ntwo\n", encoding="utf-8")
    VersionStore(doc).save()
    doc.write_text("one\nTWO\nthree\n", encoding="utf-8")
    VersionStore(doc).save()
    assert run(["diff", str(doc), "1", "2"]) == 0
    out = capsys.readouterr().out
    assert "- two" in out and "+ TWO" in out and "+ three" in out


def test_cli_diff_missing_version(tmp_path, capsys):
    doc = tmp_path / "f.txt"
    doc.write_text("x\n", encoding="utf-8")
    VersionStore(doc).save()
    assert run(["diff", str(doc), "1", "9"]) == 1
    assert "не найдена" in capsys.readouterr().err

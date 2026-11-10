import hashlib

import pytest

from cfgctl.scanner import ScanError, scan


def test_empty_directory(tmp_path):
    assert scan(tmp_path) == {}


def test_relative_paths_size_and_sha(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "f.txt").write_bytes(b"hello")
    r = scan(tmp_path)
    assert list(r) == ["a/f.txt"]
    assert r["a/f.txt"]["size"] == 5
    assert r["a/f.txt"]["sha256"] == hashlib.sha256(b"hello").hexdigest()


def test_default_excludes(tmp_path):
    for d in (".git", "__pycache__", "venv"):
        (tmp_path / d).mkdir()
        (tmp_path / d / "x").write_text("x")
    (tmp_path / "keep.py").write_text("1")
    assert list(scan(tmp_path)) == ["keep.py"]


def test_custom_exclude_and_skip_paths(tmp_path):
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "o").write_text("o")
    (tmp_path / "snap.json").write_text("{}")
    (tmp_path / "a.txt").write_text("a")
    r = scan(tmp_path, exclude={"build"}, skip_paths=[tmp_path / "snap.json"])
    assert list(r) == ["a.txt"]


def test_missing_directory():
    with pytest.raises(ScanError):
        scan("/definitely/not/here")

import pytest

from relman.changelog import add_release, released_versions
from relman.cli import run
from relman.release import check_tag, register, register_bump
from relman.version import VersionError, bump, parse, read_version, write_version

PYPROJECT = '[project]\nname = "x"\nversion = "1.2.3"\n'


@pytest.fixture
def proj(tmp_path):
    py, cl = tmp_path / "pyproject.toml", tmp_path / "CHANGELOG.md"
    py.write_text(PYPROJECT, encoding="utf-8")
    cl.write_text("# Changelog\n\n## [1.2.3] - 2026-01-01\n- init\n", encoding="utf-8")
    return py, cl


@pytest.mark.parametrize("bad", ["1.2", "1.2.3.4", "v1.2.3", "01.2.3", "a.b.c", "", "1.2.x"])
def test_invalid_semver(bad):
    with pytest.raises(VersionError, match="MAJOR.MINOR.PATCH"):
        parse(bad)


def test_bump_resets_lower_parts():
    assert bump("1.2.3", "major") == "2.0.0"
    assert bump("1.2.3", "minor") == "1.3.0"
    assert bump("1.2.3", "patch") == "1.2.4"
    with pytest.raises(VersionError):
        bump("1.2.3", "build")


def test_read_write_version(proj):
    py, _ = proj
    assert read_version(py) == "1.2.3"
    write_version(py, "2.0.0")
    assert read_version(py) == "2.0.0" and 'name = "x"' in py.read_text()


def test_register_updates_pyproject_and_changelog(proj):
    py, cl = proj
    assert register_bump(py, cl, "minor", ["новая функция"]) == "1.3.0"
    assert read_version(py) == "1.3.0"
    assert released_versions(cl) == ["1.3.0", "1.2.3"]
    assert "- новая функция" in cl.read_text(encoding="utf-8")


def test_duplicate_version_rejected(proj):
    py, cl = proj
    with pytest.raises(VersionError, match="уже существует"):
        register(py, cl, "1.2.3", ["x"])
    with pytest.raises(VersionError):
        add_release(cl, "1.2.3", ["x"])


def test_decrease_rejected(proj):
    py, cl = proj
    with pytest.raises(VersionError, match="уменьшать"):
        register(py, cl, "1.0.0", ["x"])
    assert read_version(py) == "1.2.3"


def test_tag_matches_version(proj):
    py, _ = proj
    assert check_tag("v1.2.3", py) == "1.2.3"


def test_tag_mismatch_missing_and_bad_format(proj):
    py, _ = proj
    with pytest.raises(VersionError, match="не соответствует"):
        check_tag("v1.2.4", py)
    with pytest.raises(VersionError, match="не указан"):
        check_tag(None, py)
    for bad in ("1.2.3", "v1.2", "release-1", "v1.2.3-rc1"):
        with pytest.raises(VersionError, match="формат тега"):
            check_tag(bad, py)


def test_missing_files(tmp_path):
    with pytest.raises(VersionError, match="не найден"):
        read_version(tmp_path / "none.toml")
    py = tmp_path / "p.toml"
    py.write_text("[project]\n", encoding="utf-8")
    with pytest.raises(VersionError, match="version"):
        read_version(py)


def test_cli_bump_and_check_tag(proj, capsys):
    py, cl = proj
    base = ["--pyproject", str(py), "--changelog", str(cl)]
    assert run([*base, "bump", "patch", "-m", "fix"]) == 0
    assert run([*base, "check-tag", "v1.2.4"]) == 0
    assert run([*base, "check-tag", "v9.9.9"]) == 1
    assert "не соответствует" in capsys.readouterr().err


def test_empty_changes_rejected(proj):
    _, cl = proj
    with pytest.raises(VersionError):
        add_release(cl, "1.3.0", [])

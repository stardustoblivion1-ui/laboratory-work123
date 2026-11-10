"""Проверка, что после разрешения конфликта сохранены функции обеих веток."""
import pytest

from taskman.cli import build_parser, run


def test_both_commands_registered():
    p = build_parser()
    assert p.parse_args(["filter"]).cmd == "filter"
    assert p.parse_args(["stats"]).cmd == "stats"


def test_filter_and_stats_work_together(tmp_path, capsys):
    db = str(tmp_path / "m.db")
    run(["--db", db, "add", "a", "--assignee", "Ivan", "--priority", "high"])
    run(["--db", db, "add", "b", "--assignee", "Petr"])
    run(["--db", db, "update", "1", "--status", "done"])
    capsys.readouterr()
    assert run(["--db", db, "filter", "--status", "done"]) == 0
    out = capsys.readouterr().out
    assert "a" in out and "Petr" not in out
    assert run(["--db", db, "stats"]) == 0
    assert "выполнено: 1 (50.0%)" in capsys.readouterr().out


def test_features_file_lists_all_functions():
    text = open("FEATURES.md", encoding="utf-8").read()
    for word in ("CRUD", "Фильтрация", "Статистика"):
        assert word in text
    assert "<<<<" not in text


def test_invalid_input_still_rejected(tmp_path, capsys):
    assert run(["--db", str(tmp_path / "e.db"), "add", "", "--assignee", "x"]) == 1
    assert "Ошибка" in capsys.readouterr().err


@pytest.mark.parametrize("cmd", ["list", "stats", "filter"])
def test_empty_db_commands(tmp_path, cmd):
    assert run(["--db", str(tmp_path / "z.db"), cmd]) == 0

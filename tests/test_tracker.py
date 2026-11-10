import pytest

from tracker.models import TrackerError
from tracker.store import ChangeTracker


@pytest.fixture
def tr(tmp_path):
    return ChangeTracker(tmp_path / "c.json")


def test_add_generates_unique_ids(tr):
    a = tr.add("Ivan", "feature", "one")
    b = tr.add("Ivan", "bugfix", "two")
    assert a.id != b.id and a.status == "planned"


def test_duplicate_id_rejected(tr):
    tr.add("Ivan", "feature", "one", change_id="X-1")
    with pytest.raises(TrackerError):
        tr.add("Petr", "feature", "dup", change_id="X-1")


def test_valid_transitions(tr):
    c = tr.add("Ivan", "feature", "one")
    assert tr.set_status(c.id, "in_progress").status == "in_progress"
    assert tr.set_status(c.id, "done").status == "done"


def test_invalid_transition_rejected(tr):
    c = tr.add("Ivan", "feature", "one")
    with pytest.raises(TrackerError):
        tr.set_status(c.id, "done")      # planned -> done запрещено


def test_unknown_status_rejected(tr):
    c = tr.add("Ivan", "feature", "one")
    with pytest.raises(TrackerError):
        tr.set_status(c.id, "cancelled")


def test_persistence_after_restart(tmp_path):
    p = tmp_path / "c.json"
    t1 = ChangeTracker(p)
    c = t1.add("Ivan", "docs", "readme")
    t1.set_status(c.id, "in_progress")
    t2 = ChangeTracker(p)                 # «перезапуск»
    assert t2.get(c.id).status == "in_progress"


def test_invalid_type_and_empty_fields(tr):
    with pytest.raises(TrackerError):
        tr.add("Ivan", "magic", "x")
    with pytest.raises(TrackerError):
        tr.add("  ", "feature", "x")


def test_link_commit_validation(tr):
    c = tr.add("Ivan", "feature", "x")
    assert tr.link_commit(c.id, "ABCDEF1").commit_hash == "abcdef1"
    with pytest.raises(TrackerError):
        tr.link_commit(c.id, "zzz")


def test_corrupted_file(tmp_path):
    p = tmp_path / "c.json"
    p.write_text("not json", encoding="utf-8")
    with pytest.raises(TrackerError):
        ChangeTracker(p)


def test_filtering_by_author_type_status(tr):
    a = tr.add("Ivan", "feature", "a")
    tr.add("Petr", "bugfix", "b")
    tr.set_status(a.id, "in_progress")
    assert [c.id for c in tr.find(author="Ivan")] == [a.id]
    assert len(tr.find(type_="bugfix")) == 1
    assert [c.id for c in tr.find(status="in_progress")] == [a.id]
    assert tr.find(author="Nobody") == []

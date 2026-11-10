import pytest

from fvm.storage import VersionError, VersionStore


def make(tmp_path, text="a\nb\n"):
    doc = tmp_path / "doc.txt"
    doc.write_text(text, encoding="utf-8")
    return doc, VersionStore(doc)


def test_save_creates_versions_with_ids_and_time(tmp_path):
    doc, st = make(tmp_path)
    e1 = st.save("first")
    doc.write_text("a\nb\nc\n", encoding="utf-8")
    e2 = st.save()
    assert (e1["id"], e2["id"]) == (1, 2)
    assert e1["time"] and e1["comment"] == "first"
    assert len(st.list_versions()) == 2


def test_restore_returns_old_content_and_keeps_history(tmp_path):
    doc, st = make(tmp_path, "v1\n")
    st.save()
    doc.write_text("v2\n", encoding="utf-8")
    st.save()
    st.restore(1)
    assert doc.read_text(encoding="utf-8") == "v1\n"
    assert len(st.list_versions()) == 3          # история не уничтожена
    assert st.get_text(2) == "v2\n"


def test_missing_version_raises(tmp_path):
    _, st = make(tmp_path)
    st.save()
    with pytest.raises(VersionError):
        st.get_text(99)
    with pytest.raises(VersionError):
        st.restore(5)


@pytest.mark.parametrize("bad", [0, -1, "x", None, True])
def test_invalid_version_number(tmp_path, bad):
    _, st = make(tmp_path)
    st.save()
    with pytest.raises(VersionError):
        st.get_text(bad)


def test_save_missing_file(tmp_path):
    st = VersionStore(tmp_path / "nope.txt")
    with pytest.raises(VersionError):
        st.save()


def test_history_survives_new_store_instance(tmp_path):
    doc, st = make(tmp_path)
    st.save()
    assert len(VersionStore(doc).list_versions()) == 1


def test_corrupted_index(tmp_path):
    doc, st = make(tmp_path)
    st.save()
    st.index_file.write_text("{broken", encoding="utf-8")
    with pytest.raises(VersionError):
        st.list_versions()

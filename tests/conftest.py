import pytest

from scmtrace.registry import Registry


@pytest.fixture
def root(tmp_path):
    r = tmp_path / "proj"
    r.mkdir()
    (r / "app.py").write_text("print('v1')\n")
    (r / "lib.py").write_text("X = 1\n")
    return r


@pytest.fixture
def reg(tmp_path):
    x = Registry(str(tmp_path / "t.db"))
    yield x
    x.close()

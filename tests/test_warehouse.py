import pytest

from warehouse.cli import run
from warehouse.db import Warehouse, WarehouseError


@pytest.fixture
def w(tmp_path):
    x = Warehouse(str(tmp_path / "w.db"))
    x.add_category("Инструменты")
    x.add_product("Молоток", "Инструменты", 10)
    yield x
    x.close()


def test_add_and_get_product(w):
    p = w.get_product("Молоток")
    assert p["quantity"] == 10 and p["category"] == "Инструменты"


def test_duplicate_product_rejected(w):
    with pytest.raises(WarehouseError):
        w.add_product("Молоток")


def test_duplicate_category_rejected(w):
    with pytest.raises(WarehouseError):
        w.add_category("Инструменты")


def test_receive_increases_stock(w):
    assert w.receive("Молоток", 5) == 15


def test_issue_decreases_stock(w):
    assert w.issue("Молоток", 4) == 6


def test_insufficient_stock(w):
    with pytest.raises(WarehouseError, match="Недостаточно"):
        w.issue("Молоток", 11)
    assert w.get_product("Молоток")["quantity"] == 10


@pytest.mark.parametrize("bad", [0, -3, 1.5, "2", True])
def test_invalid_quantity(w, bad):
    with pytest.raises(WarehouseError):
        w.receive("Молоток", bad)
    with pytest.raises(WarehouseError):
        w.issue("Молоток", bad)


def test_negative_initial_stock_rejected(w):
    with pytest.raises(WarehouseError):
        w.add_product("Гвозди", None, -1)


def test_unknown_product_and_category(w):
    with pytest.raises(WarehouseError):
        w.issue("Нет такого", 1)
    with pytest.raises(WarehouseError):
        w.add_product("Пила", "Несуществующая")


def test_search_case_insensitive(w):
    assert [r["name"] for r in w.search("МОЛ")] == ["Молоток"]
    assert w.search("xyz") == []


def test_delete_requires_zero_stock(w):
    with pytest.raises(WarehouseError):
        w.delete_product("Молоток")
    w.issue("Молоток", 10)
    w.delete_product("Молоток")
    with pytest.raises(WarehouseError):
        w.get_product("Молоток")


def test_journal_records_operations(w):
    w.receive("Молоток", 2, "поставка")
    w.issue("Молоток", 1)
    kinds = [j["kind"] for j in w.journal()]
    assert kinds == ["receipt", "receipt", "issue"]      # начальный остаток + поставка + списание


def test_stock_report_and_rename(w):
    w.rename_product("Молоток", "Молоток большой")
    assert w.stock_report() == [
        {"name": "Молоток большой", "category": "Инструменты", "quantity": 10}]


def test_cli_end_to_end(tmp_path, capsys):
    db = str(tmp_path / "c.db")
    assert run(["--db", db, "product", "add", "Гвозди", "--qty", "5"]) == 0
    assert run(["--db", db, "issue", "Гвозди", "9"]) == 1
    assert "Недостаточно" in capsys.readouterr().err

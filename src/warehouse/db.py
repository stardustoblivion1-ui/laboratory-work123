"""Складской учёт: товары, категории, остатки, операции."""
from __future__ import annotations

import sqlite3
from datetime import datetime


class WarehouseError(Exception):
    """Ошибка складских операций."""


def _qty(q) -> int:
    if isinstance(q, bool) or not isinstance(q, int) or q <= 0:
        raise WarehouseError("Количество должно быть положительным целым числом")
    return q


class Warehouse:
    def __init__(self, path: str = "warehouse.db"):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE);
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category_id INTEGER REFERENCES categories(id),
                quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0));
            CREATE TABLE IF NOT EXISTS operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TEXT NOT NULL,
                product_id INTEGER NOT NULL,
                kind TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                note TEXT NOT NULL DEFAULT '');
            """
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # --- категории ---
    def add_category(self, name: str) -> int:
        if not name.strip():
            raise WarehouseError("Название категории не может быть пустым")
        try:
            cur = self.conn.execute("INSERT INTO categories (name) VALUES (?)", (name.strip(),))
        except sqlite3.IntegrityError:
            raise WarehouseError(f"Категория «{name}» уже существует") from None
        self.conn.commit()
        return cur.lastrowid

    def _category_id(self, name: str | None) -> int | None:
        if name is None:
            return None
        row = self.conn.execute("SELECT id FROM categories WHERE name=?", (name,)).fetchone()
        if row is None:
            raise WarehouseError(f"Категория «{name}» не найдена")
        return row["id"]

    # --- товары (CRUD) ---
    def add_product(self, name: str, category: str | None = None, quantity: int = 0) -> int:
        if not name.strip():
            raise WarehouseError("Название товара не может быть пустым")
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 0:
            raise WarehouseError("Начальный остаток не может быть отрицательным")
        cid = self._category_id(category)
        try:
            cur = self.conn.execute(
                "INSERT INTO products (name, category_id, quantity) VALUES (?,?,?)",
                (name.strip(), cid, quantity))
        except sqlite3.IntegrityError:
            raise WarehouseError(f"Товар «{name}» уже существует") from None
        pid = cur.lastrowid
        if quantity:
            self._log(pid, "receipt", quantity, "начальный остаток")
        self.conn.commit()
        return pid

    def get_product(self, name: str) -> dict:
        row = self.conn.execute(
            "SELECT p.id, p.name, c.name AS category, p.quantity FROM products p "
            "LEFT JOIN categories c ON c.id = p.category_id WHERE p.name=?", (name,)).fetchone()
        if row is None:
            raise WarehouseError(f"Товар «{name}» не найден")
        return dict(row)

    def rename_product(self, name: str, new_name: str) -> None:
        pid = self.get_product(name)["id"]
        if not new_name.strip():
            raise WarehouseError("Название товара не может быть пустым")
        try:
            self.conn.execute("UPDATE products SET name=? WHERE id=?", (new_name.strip(), pid))
        except sqlite3.IntegrityError:
            raise WarehouseError(f"Товар «{new_name}» уже существует") from None
        self.conn.commit()

    def delete_product(self, name: str) -> None:
        p = self.get_product(name)
        if p["quantity"] > 0:
            raise WarehouseError("Нельзя удалить товар с ненулевым остатком")
        self.conn.execute("DELETE FROM products WHERE id=?", (p["id"],))
        self.conn.commit()

    def search(self, text: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT p.name, c.name AS category, p.quantity FROM products p "
            "LEFT JOIN categories c ON c.id=p.category_id "
            "WHERE lower(p.name) LIKE ? ORDER BY p.name", (f"%{text.lower()}%",))
        return [dict(r) for r in rows]

    # --- операции ---
    def _log(self, pid: int, kind: str, qty: int, note: str) -> None:
        self.conn.execute(
            "INSERT INTO operations (time, product_id, kind, quantity, note) VALUES (?,?,?,?,?)",
            (datetime.now().isoformat(timespec="seconds"), pid, kind, qty, note))

    def receive(self, name: str, qty: int, note: str = "") -> int:
        qty = _qty(qty)
        p = self.get_product(name)
        self.conn.execute("UPDATE products SET quantity = quantity + ? WHERE id=?", (qty, p["id"]))
        self._log(p["id"], "receipt", qty, note)
        self.conn.commit()
        return p["quantity"] + qty

    def issue(self, name: str, qty: int, note: str = "") -> int:
        qty = _qty(qty)
        p = self.get_product(name)
        if p["quantity"] < qty:
            raise WarehouseError(
                f"Недостаточно товара «{name}»: на складе {p['quantity']}, запрошено {qty}")
        self.conn.execute("UPDATE products SET quantity = quantity - ? WHERE id=?", (qty, p["id"]))
        self._log(p["id"], "issue", qty, note)
        self.conn.commit()
        return p["quantity"] - qty

    # --- отчёты ---
    def stock_report(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT p.name, COALESCE(c.name,'—') AS category, p.quantity FROM products p "
            "LEFT JOIN categories c ON c.id=p.category_id ORDER BY c.name, p.name")
        return [dict(r) for r in rows]

    def journal(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT o.id, o.time, p.name AS product, o.kind, o.quantity, o.note "
            "FROM operations o LEFT JOIN products p ON p.id=o.product_id ORDER BY o.id")
        return [dict(r) for r in rows]

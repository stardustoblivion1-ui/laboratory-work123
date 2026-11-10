# Отчёт по практической работе №19–20 — задание 5

**Тема:** Складская система с непрерывной интеграцией  
**Репозиторий:** `warehouse-ci` (локальный Git-репозиторий; ссылка на GitHub — _вставить_)

## 1. Цель работы
Разработать складской учёт на SQLite и настроить CI в GitHub Actions (ruff + pytest на push и pull_request, Python 3.11/3.12).

## 2. Схема алгоритма
```
receive: проверка qty>0 → UPDATE quantity+qty → запись в журнал
issue: проверка qty>0 и остаток ≥ qty → UPDATE quantity−qty → журнал; иначе ошибка «Недостаточно»
CI: checkout → setup-python (матрица 3.11/3.12) → установка → ruff → pytest
```

## 3. Описание архитектуры
`db.py` — Warehouse (товары, категории, операции, отчёты, CHECK quantity>=0 в схеме); `cli.py`; `.github/workflows/ci.yml`.

## 4. Основные фрагменты кода
**`src/warehouse/db.py` — `Warehouse.issue`**
```python
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
```

**`src/warehouse/db.py` — `Warehouse.search`**
```python
    def search(self, text: str) -> list[dict]:
        # поиск в Python: SQLite lower() не учитывает регистр кириллицы
        needle = text.lower()
        rows = self.conn.execute(
            "SELECT p.name, c.name AS category, p.quantity FROM products p "
            "LEFT JOIN categories c ON c.id=p.category_id ORDER BY p.name")
        return [dict(r) for r in rows if needle in r["name"].lower()]
```

## 5. Результаты запуска
### Тесты (pytest)
```
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-9.2.0, pluggy-1.7.0 -- /Users/wincerdion/Documents/123/scm_practice/.venv/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/wincerdion/Documents/123/scm_practice/warehouse-ci
configfile: pyproject.toml
testpaths: tests
collecting ... collected 18 items

tests/test_warehouse.py::test_add_and_get_product PASSED                 [  5%]
tests/test_warehouse.py::test_duplicate_product_rejected PASSED          [ 11%]
tests/test_warehouse.py::test_duplicate_category_rejected PASSED         [ 16%]
tests/test_warehouse.py::test_receive_increases_stock PASSED             [ 22%]
tests/test_warehouse.py::test_issue_decreases_stock PASSED               [ 27%]
tests/test_warehouse.py::test_insufficient_stock PASSED                  [ 33%]
tests/test_warehouse.py::test_invalid_quantity[0] PASSED                 [ 38%]
tests/test_warehouse.py::test_invalid_quantity[-3] PASSED                [ 44%]
tests/test_warehouse.py::test_invalid_quantity[1.5] PASSED               [ 50%]
tests/test_warehouse.py::test_invalid_quantity[2] PASSED                 [ 55%]
tests/test_warehouse.py::test_invalid_quantity[True] PASSED              [ 61%]
tests/test_warehouse.py::test_negative_initial_stock_rejected PASSED     [ 66%]
tests/test_warehouse.py::test_unknown_product_and_category PASSED        [ 72%]
tests/test_warehouse.py::test_search_case_insensitive PASSED             [ 77%]
tests/test_warehouse.py::test_delete_requires_zero_stock PASSED          [ 83%]
tests/test_warehouse.py::test_journal_records_operations PASSED          [ 88%]
tests/test_warehouse.py::test_stock_report_and_rename PASSED             [ 94%]
tests/test_warehouse.py::test_cli_end_to_end PASSED                      [100%]

============================== 18 passed in 0.05s ==============================
```
### Статический анализ (ruff)
```
All checks passed!
```
### Git: ветки, коммиты, теги
Ветки: main; коммитов: 6; теги: v1.0.0
```
* 5674959 (HEAD -> main, tag: v1.0.0) docs: CI evidence (failing and fixed runs)
* 41fa5cf fix: remove unused import reported by ruff (CI green)
* 985f57f ci: add GitHub Actions workflow (ruff + pytest, Python 3.11/3.12)
* 9fd2f86 fix: case-insensitive search for Cyrillic names
* 294f55a feat: SQLite warehouse (products, categories, receipts/issues, search, reports)
* 7ecbcbd chore: init project, README, pyproject
```

## Подтверждение CI
Workflow-файлы лежат в `.github/workflows/`. Ссылки/скриншоты запусков GitHub Actions обязательны для заданий 5–9 — вставьте их после `git push` в раздел ниже (шаблон — `docs/CI_EVIDENCE.md` там, где он есть):
- Ссылка на репозиторий: _вставить_
- Ссылки на запуски Actions: _вставить_

## 6. Связь с конфигурационным управлением
Непрерывная интеграция автоматически проверяет каждое изменение. Один коммит намеренно содержит нарушение ruff (F401), следующий — исправление; хэши в `docs/CI_EVIDENCE.md`.

## 7. Ограничения системы
Реальные запуски GitHub Actions требуют публикации репозитория — ссылки нужно вставить в `docs/CI_EVIDENCE.md`; CD/деплой не реализован.

## 8. Вывод
В ходе работы выполнено задание 5: «Складская система с непрерывной интеграцией». Функциональные требования реализованы, автоматические тесты проходят, изменения оформлены в Git (ветки, содержательные коммиты, тег). Результаты подтверждают работоспособность решения в пределах перечисленных ограничений.

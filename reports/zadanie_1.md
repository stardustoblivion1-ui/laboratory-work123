# Отчёт по практической работе №19–20 — задание 1

**Тема:** Менеджер версий текстовых документов  
**Репозиторий:** `file-version-manager` (локальный Git-репозиторий; ссылка на GitHub — _вставить_)

## 1. Цель работы
Научиться хранить версии текстовых файлов, сравнивать их построчно и безопасно восстанавливать, используя Git (ветвление, слияние, тег).

## 2. Схема алгоритма
```
save: прочитать файл → присвоить id=N+1 и время → записать vNNNN.txt и запись в index.json
diff a b: прочитать версии → difflib.ndiff → пометки '+', '-', ' '
restore n: прочитать версию n → записать в рабочий файл → сохранить как НОВУЮ версию (история не удаляется)
```

## 3. Описание архитектуры
`storage.py` — VersionStore (хранилище и восстановление); `compare.py` — построчное сравнение; `cli.py` — команды save/list/show/restore/diff. Хранилище: каталог `.fvm/<документ>/` с `index.json`.

## 4. Основные фрагменты кода
**`src/fvm/storage.py` — `VersionStore.restore`**
```python
    def restore(self, version: int) -> dict:
        """Восстанавливает версию в рабочий файл; история не удаляется —
        восстановленное состояние записывается как новая версия."""
        text = self.get_text(version)
        self.document.write_text(text, encoding="utf-8")
        return self.save_text(text, comment=f"restore of v{version}")
```

**`src/fvm/compare.py` — `diff_lines`**
```python
def diff_lines(old: str, new: str) -> list[str]:
    out: list[str] = []
    for line in difflib.ndiff(old.splitlines(), new.splitlines()):
        if line.startswith("+ "):
            out.append("+ " + line[2:])
        elif line.startswith("- "):
            out.append("- " + line[2:])
        elif line.startswith("  "):
            out.append("  " + line[2:])
    return out
```

## 5. Результаты запуска
### Тесты (pytest)
```
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-9.2.0, pluggy-1.7.0 -- /Users/wincerdion/Documents/123/scm_practice/.venv/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/wincerdion/Documents/123/scm_practice/file-version-manager
configfile: pyproject.toml
testpaths: tests
collecting ... collected 15 items

tests/test_compare.py::test_diff_marks_added_and_removed PASSED          [  6%]
tests/test_compare.py::test_identical_texts_have_no_changes PASSED       [ 13%]
tests/test_compare.py::test_cli_diff_between_two_real_states PASSED      [ 20%]
tests/test_compare.py::test_cli_diff_missing_version PASSED              [ 26%]
tests/test_storage.py::test_save_creates_versions_with_ids_and_time PASSED [ 33%]
tests/test_storage.py::test_restore_returns_old_content_and_keeps_history PASSED [ 40%]
tests/test_storage.py::test_missing_version_raises PASSED                [ 46%]
tests/test_storage.py::test_invalid_version_number[0] PASSED             [ 53%]
tests/test_storage.py::test_invalid_version_number[-1] PASSED            [ 60%]
tests/test_storage.py::test_invalid_version_number[x] PASSED             [ 66%]
tests/test_storage.py::test_invalid_version_number[None] PASSED          [ 73%]
tests/test_storage.py::test_invalid_version_number[True] PASSED          [ 80%]
tests/test_storage.py::test_save_missing_file PASSED                     [ 86%]
tests/test_storage.py::test_history_survives_new_store_instance PASSED   [ 93%]
tests/test_storage.py::test_corrupted_index PASSED                       [100%]

============================== 15 passed in 0.05s ==============================
```
### Статический анализ (ruff)
```
All checks passed!
```
### Git: ветки, коммиты, теги
Ветки: feature-compare, main; коммитов: 7; теги: v1.0.0
```
* 5f2b197 (HEAD -> main, tag: v1.0.0) docs: CHANGELOG for 1.0.0
*   c8e3063 Merge branch 'feature-compare' into main
|\  
| * 02a4a4c (feature-compare) feat(cli): diff command + compare tests
| * dcf71c0 feat(compare): line-by-line diff with +/- markers
|/  
* 172f312 feat: CLI (save/list/restore/show) with error handling
* 4c5ba72 feat: version storage with save/list/restore (history preserved)
* a639c28 chore: init project structure, pyproject, README, .gitignore
```

## 6. Связь с конфигурационным управлением
Версии документа — простейшая модель конфигурационных единиц с идентификатором и временем; восстановление без потери истории соответствует требованию неизменяемости зафиксированных состояний. Работа выполнена в Git: ветка feature-compare, слияние --no-ff, аннотированный тег v1.0.0.

## 7. Ограничения системы
Только текстовые файлы UTF-8; хранение полных копий (без дельт); нет блокировок при одновременной работе.

## 8. Вывод
В ходе работы выполнено задание 1: «Менеджер версий текстовых документов». Функциональные требования реализованы, автоматические тесты проходят, изменения оформлены в Git (ветки, содержательные коммиты, тег). Результаты подтверждают работоспособность решения в пределах перечисленных ограничений.

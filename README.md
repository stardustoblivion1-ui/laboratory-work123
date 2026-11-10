# file-version-manager

Консольный менеджер версий текстовых документов (практическая работа №19–20, задание 1).

## Запуск
```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt && pip install -e .
fvm save notes.txt          # сохранить текущее состояние файла как новую версию
fvm list notes.txt          # список версий
fvm diff notes.txt 1 2      # построчное сравнение (+ добавлено, - удалено)
fvm restore notes.txt 1     # восстановить версию 1 (создаётся НОВАЯ версия, история сохраняется)
```
Версии хранятся в каталоге `.fvm/` рядом с документом.

## Тесты
```bash
pytest -v
```

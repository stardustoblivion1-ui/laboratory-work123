# Установка собранного пакета

1. Скачайте артефакт `dist` со страницы запуска «Release build» (GitHub → Actions → нужный запуск → Artifacts) и распакуйте.
2. Установите wheel:
```bash
python -m venv .venv && . .venv/bin/activate
pip install dist/release_manager-1.0.0-py3-none-any.whl
relman --help
```
Либо из sdist: `pip install dist/release_manager-1.0.0.tar.gz`.
Локальная сборка: `pip install build && python -m build`.

# Подтверждение CI и pull request'ов

Workflow `.github/workflows/ci.yml`: ruff → pytest → сборка пакета → artifact `dist`.
Локально выполнено: `ruff check .`, `pytest` (22 теста), `python -m build`.

После публикации на GitHub вставьте ссылки:
- Pull request #1 (feature-registry): _ссылка_
- Pull request #2 (feature-changes): _ссылка_
- Pull request #3 (feature-baselines): _ссылка_
- Pull request #4 (feature-release): _ссылка_
- Успешный запуск CI (Actions): _ссылка_; тег v1.0.0: _ссылка_

# release-manager

Менеджер версий Python-пакета (SemVer) и автоматизация сборки по Git-тегу (практическая работа №19–20, задание 6).

```bash
pip install -r requirements.txt && pip install -e .
relman show                                   # текущая версия из pyproject.toml
relman bump minor -m "Новая функция"          # 1.2.3 -> 1.3.0, запись в CHANGELOG.md
relman set 2.0.0 -m "Ломающее изменение"      # явная версия (нельзя уменьшать/повторять)
relman check-tag v1.0.0                       # проверка тега (используется только релизным workflow)
pytest -v
```

## GitHub Actions
- `ci.yml` — на `push` и `pull_request`: только `pytest`, тег не проверяется.
- `release.yml` — только на тег `v*`: `relman check-tag` → `pytest` → `python -m build` (wheel + sdist) → Artifacts.
  При несоответствии тега и версии (или неверном формате) job завершается ошибкой **до** сборки, артефакты не создаются.

Установка собранного пакета — `INSTALL.md`. Подтверждения запусков — `docs/CI_EVIDENCE.md`.

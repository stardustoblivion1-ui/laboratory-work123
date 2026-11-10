# Отчёт о разрешении конфликта слияния

## 1. Коммиты до слияния
```
*   ceb26d4 (HEAD -> main) Merge branch 'feature-statistics' (resolved conflicts in cli.py and FEATURES.md, kept both features)
|\  
| * b6edc0a (feature-statistics) feat(statistics): completion statistics command
* |   2d5cfad Merge branch 'feature-filter'
|\ \  
| |/  
|/|   
| * eb3390a (feature-filter) feat(filter): filter tasks by assignee, priority and status
|/  
*   098ec59 Merge branch 'feature-tasks'
|\  
| * 9502444 (feature-tasks) feat(tasks): SQLite CRUD with validation and CLI
|/  
* d0bb952 chore: init project, README, FEATURES.md
```

## 2. Конфликт
Ветки `feature-filter` и `feature-statistics` независимо изменили одни и те же места в `src/taskman/cli.py` (импорты, регистрация подкоманд, обработчик) и в `FEATURES.md`.

```
CONFLICT (content): Merge conflict in FEATURES.md
CONFLICT (content): Merge conflict in src/taskman/cli.py
Automatic merge failed; fix conflicts and then commit the result.
```

Фрагмент `git diff` с маркерами:
```diff
diff --cc FEATURES.md
index bd5dbb8,9a306a5..0000000
--- a/FEATURES.md
+++ b/FEATURES.md
@@@ -1,4 -1,4 +1,8 @@@
  # Реализованные функции (учебный файл для демонстрации конфликта слияния)
  
  - CRUD задач в SQLite (`add/list/update/delete`)
++<<<<<<< HEAD
 +- Фильтрация по исполнителю, приоритету и статусу (`filter`)
++=======
+ - Статистика выполнения (`stats`)
++>>>>>>> feature-statistics
diff --cc src/taskman/cli.py
index 0d73208,2b9d1bd..0000000
--- a/src/taskman/cli.py
+++ b/src/taskman/cli.py
@@@ -5,7 -5,7 +5,11 @@@ import argpars
  import sys
  
  from .db import TaskDB, TaskError
++<<<<<<< HEAD
 +from .filters import filter_tasks
++=======
+ from .stats import statistics
++>>>>>>> feature-statistics
  
  
  def fmt(t: dict) -> str:
@@@ -29,10 -29,7 +33,14 @@@ def build_parser() -> argparse.Argument
          u.add_argument(f"--{f}")
      sub.add_parser("delete").add_argument("id", type=int)
      # --- extra commands (сюда добавляют новые подкоманды) ---
++<<<<<<< HEAD
 +    f = sub.add_parser("filter")
 +    f.add_argument("--assignee")
 +    f.add_argument("--priority")
 +    f.add_argument("--status")
++=======
+     sub.add_parser("stats")
++>>>>>>> feature-statistics
      return p
  
  
@@@ -52,9 -49,11 +60,17 @@@ def run(argv=None) -> int
```

## 3. Разрешение
Маркеры `<<<<<<<`, `=======`, `>>>>>>>` удалены, оставлены **обе** части: команды `filter` и `stats`, оба импорта и обе строки в `FEATURES.md`. Добавлен `tests/test_after_merge.py`.

## 4. Итоговый merge commit
```
ceb26d4804ae49d130475b12311f18594fcfbbdf
Merge branch 'feature-statistics' (resolved conflicts in cli.py and FEATURES.md, kept both features)
```

# Демонстрация полного сценария

```
$ scmp project add shop
Проект зарегистрирован, id = 1
$ scmp ci add shop api
CI shop/api@1.0.0 зарегистрирована
$ scmp baseline create shop BL-1
Baseline BL-1 утверждена
$ scmp change create shop "Новый эндпоинт /orders"
Создан запрос 1
$ scmp change apply 1 api 1.1.0
Ошибка: Запрос 1 нельзя применить: статус «proposed», требуется «approved»
$ scmp change decide 1 approve --by Иванов --note согласовано
Статус: approved
$ scmp change apply 1 api 1.1.0 --hash 9f2c1a
Запрос 1 применён: api@1.1.0
$ scmp baseline create shop BL-2
Baseline BL-2 утверждена
$ scmp baseline compare shop BL-1 BL-2
{
  "added": [],
  "removed": [],
  "changed": {
    "api": {
      "from": "1.0.0",
      "to": "1.1.0"
    }
  }
}
$ scmp release register shop 1.1.0 --baseline BL-2
Релиз 1.1.0 зарегистрирован на BL-2
$ scmp history shop
2026-11-10T17:01:14  project.register shop
2026-11-10T17:01:14  ci.register      api@1.0.0
2026-11-10T17:01:15  baseline.create  BL-1 (1 CI)
2026-11-10T17:01:15  change.create    #1 Новый эндпоинт /orders
2026-11-10T17:01:15  change.approved  #1 by Иванов
2026-11-10T17:01:15  change.apply     #1 api@1.1.0
2026-11-10T17:01:15  baseline.create  BL-2 (1 CI)
2026-11-10T17:01:15  release.register 1.1.0 on BL-2
```

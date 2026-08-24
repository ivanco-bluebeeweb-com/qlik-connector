# Qlik Connector — история цен

## 2026-08-24 — первичный прайсинг (per_action, каноническая шкала {0,8,16,20,40,60})

Выставлено ДО `submit_for_review`, после чистого деплоя (21/21), согласно
`PRICING_POLICY.md`.

| Функция | Цена | Обоснование |
|---|---|---|
| `connect_qlik` | 0 | Настройка доступа — по правилу §2 не взимаем плату за connect/disconnect |
| `disconnect_qlik` | 0 | Удаление доступа — то же правило |
| `list_connections` | 0 | Чисто локальный инвентарь сохранённых подключений |
| `list_spaces` | 8 | `list_*` — простое чтение |
| `list_apps` | 8 | `list_*` — простое чтение |
| `get_app` | 8 | `get_*` — одиночное чтение |
| `list_reload_tasks` | 8 | `list_*` — простое чтение расписаний |
| `get_reload` | 8 | `get_*` — простое чтение статуса reload |
| `list_reload_task_executions` | 8 | `list_*` — простое чтение истории |
| `list_data_connections` | 8 | `list_*` — простое чтение |
| `list_users` | 8 | `list_*` — простое чтение |
| `run_reload_task` | 20 | Реально запускает работу в проде пользователя прямо сейчас (data reload в Qlik Cloud) |
| `audit_instance_health` | 40 | Агрегирует несколько списков (spaces+apps+reload tasks) в один вызов — самая тяжёлая операция |

Итого: 3 бесплатных, 8×8, 1×20, 1×40.

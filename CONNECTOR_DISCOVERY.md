# Qlik Connector — Discovery

**Статус:** discovery завершён, готов к PREPARATION.md
**Источники:** qlik.dev/apis/rest/ (Qlik Cloud REST API), qlik.dev/authenticate/
(API key auth), qlik.dev/apis/rest/reload-tasks/ (reload tasks).

## 1. Что за продукт

Qlik — Gartner Leader ABI Platforms, associative-engine BI. Сейчас — прежде
всего **Qlik Cloud** (SaaS, `<tenant>.<region>.qlikcloud.com`). Старый Qlik
Sense Enterprise on Windows (QSEoW, self-hosted) использует ОТДЕЛЬНЫЙ
Repository Service API (QRS, XML/SOAP-подобный) и Engine API (WebSocket) —
вне scope v1 (см. §5).

## 2. API-поверхность

REST API: `https://<tenant>.<region>.qlikcloud.com/api/v1/*`.

- **Apps** — Qlik-приложения (аналог workbook/report), хранятся в Spaces.
- **Spaces** — контейнеры доступа: `personal` (только у владельца),
  `shared` (открытый список участников), `managed` (строгий RBAC,
  Enterprise). Список apps в UI должен группироваться по Space.
- **Reload tasks** (`/reload-tasks`) — расписания обновления данных
  приложения; ручной запуск через `POST /reload-tasks/{id}/actions/start`
  запускает reload (асинхронно) → статус читается через
  `GET /reloads/{id}` (стандартный async job/poll паттерн, как dataset
  refresh в Power BI / extract refresh в Tableau).
- **Data connections** (`/data-connections`) — источники данных, к которым
  подключены приложения.
- **Automations** (`/automations`) — Qlik Application Automation, отдельный
  no-code automation слой поверх приложений (кандидат Ярус 2/3).
- **Users** (`/users`) — пользователи тенанта, роли/доступ.
- **Collections** (`/collections`) — избранное/группировки приложений
  (кандидат Ярус 2/3).

## 3. Авторизация

**API key** (Bearer token) — генерируется в Management Console
(`Settings > API keys`), время жизни настраивается при создании (может
быть без срока). Значительно проще, чем Tableau (нет сессии/переавторизации)
и ближе к модели Klaviyo/Shopify/HubSpot Private App: один статичный токен,
`Authorization: Bearer <key>` на каждый запрос.

## 4. Reload tasks — паттерн async job

`POST /reload-tasks/{taskId}/actions/start` возвращает `reloadId` сразу;
реальный статус (`QUEUED`/`RUNNING`/`SUCCEEDED`/`FAILED`) читается через
`GET /reloads/{reloadId}`. Тот же паттерн переиспользуем 1:1 у Power BI/
Tableau — единый `run_x_refresh` → `get_job`-подобная пара.

## 5. Explicit out-of-scope (v1)

- QSEoW (self-hosted Repository/Engine API) — отдельная, устаревающая
  архитектура; не строим в этой версии, только Qlik Cloud.
- NPrinting (PDF-рассылки по расписанию) — отдельный продукт/API, Ярус 2/3.
- Application Automation (`/automations`) — отдельный no-code слой, Ярус 2/3.

## 6. Ярус 1 (v1 scope, максимальный функционал в рамках Qlik Cloud REST API)

connect/disconnect/list_connections, list_spaces, list_apps (по space),
get_app, list_reload_tasks, run_reload_task (start), get_reload (job
status), list_reload_task_history, list_data_connections, list_users,
audit_instance_health (apps + failed reloads за 24ч + spaces count).

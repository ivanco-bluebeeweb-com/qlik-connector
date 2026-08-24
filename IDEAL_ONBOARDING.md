# Qlik Connector — идеальный первый запуск

Источник: `ONBOARDING_FIRST_LAUNCH_STANDARD.md`. Целевой пользователь:
BI/Data аналитик или Qlik Cloud tenant админ.

## 1. Credential type
API key (Bearer token) + tenant hostname
(`<tenant>.<region>.qlikcloud.com`) — статичный токен, без сессии/refresh.

## 2. Идеальный флоу

1. **Первое открытие** — `Empty` со ссылкой на создание API key
   (Management Console > Settings > API keys) и явным пояснением, где найти
   tenant hostname (виден прямо в адресной строке браузера при работе в
   Qlik Cloud).
2. **Форма** — tenant_hostname (placeholder: `mytenant.us.qlikcloud.com`) +
   api_key, оба с лейблами и контекстными placeholder-ами, плюс
   необязательный `label`.
3. **После успешного подключения** — сразу список Spaces с числом apps в
   каждом (personal/shared/managed помечены явным Badge); если Spaces
   пусты — точное объяснение "API key подключен, но у пользователя нет
   доступа ни к одному Space" с инструкцией куда идти.
4. **Health snapshot сразу после connect** — сколько apps, сколько failed
   reload-задач за последние 24ч, сколько Spaces доступно —
   POST_CONNECT_EXPERIENCE принцип, применённый с первого взгляда.
5. **Ошибка 401 на api_key** — конкретное сообщение "API key недействителен
   или отозван — создайте новый в Management Console" с прямой ссылкой, не
   общий "Unauthorized".
6. **Reload task упал (FAILED)** — карточка задачи явно показывает script
   log excerpt/ошибку из ответа `GET /reloads/{id}`, а не просто статус
   "Failed" без объяснения.

## 3. Разница с реализацией сейчас
См. UI_COMPONENT_PLAN.md §0 — реализация ниже строго из существующего
словаря `imperal_sdk.ui`, без компромиссов относительно этого идеального
флоу (Qlik Cloud REST API уже даёт всё необходимое для шагов 1-6).

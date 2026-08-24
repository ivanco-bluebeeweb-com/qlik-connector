# Qlik Connector — Preparation

## 1. Паспорт приложения

- **Название:** Qlik Connector
- **Короткое описание:** Управление Qlik Cloud приложениями, Spaces и
  reload-задачами прямо из Imperal — запуск обновлений, мониторинг заданий
  и доступ пользователей.
- **Владелец продукта:** vlad@bluebeeweb.com
- **Дата подготовки:** 2026-08-24
- **Почему сейчас:** BI/Аналитика — новая категория портфеля (см.
  `Docs/session-notes/NEXT_12_CATEGORIES_RESEARCH.md` §5); Qlik — Gartner
  Leader ABI Platforms, разнообразит портфель BI-коннекторов
  associative-engine альтернативой Power BI/Tableau.
- **Scope:** максимальный функционал в рамках Qlik Cloud REST API (QSEoW
  self-hosted и NPrinting явно вне scope v1, см. CONNECTOR_DISCOVERY.md §5).

## 2. Проблема в человеческих словах

Когда **BI/Data аналитик или Qlik Cloud админ** сталкивается с
**необходимостью проверить упавшую reload-задачу, найти нужное приложение
среди Spaces или дать/забрать доступ пользователю**, ей приходится
**открывать отдельный веб-интерфейс Qlik Cloud, переключаться между Spaces
вручную и искать нужный reload в отдельном журнале задач**, из-за чего
возникает **задержка в реакции на упавшие обновления данных и отсутствие
единого места мониторинга Qlik рядом с остальными операционными системами
компании**.

## 3. Пользователи и роли

- **BI/Data аналитик** — публикует приложения, следит за reload-задачами,
  чинит упавшие обновления.
- **Qlik Cloud tenant админ** — управляет пользователями/Spaces, настраивает
  data connections.
- **Руководитель/консьюмер дашбордов** — не имеет прямого доступа к
  приложению, выигрывает от свежих данных.

## 4. Credential type и авторизация

API key (Bearer token) + tenant hostname — статичный токен, без сессии/
переавторизации (см. CONNECTOR_DISCOVERY.md §3). Простейшая модель среди
трёх BI-коннекторов этой партии.

## 5. Ярус функционала (максимум в рамках API)

**Ярус 1 (v1, всё что даёт REST API):**
connect_qlik/disconnect_qlik/list_connections, list_spaces, list_apps,
get_app, list_reload_tasks, run_reload_task, get_reload,
list_reload_task_executions, list_data_connections, list_users,
audit_instance_health.

**Ярус 2/3 (явно из scope, задокументировано, не выдумываем эндпоинты):**
Application Automation API, NPrinting, Collections, QSEoW self-hosted.

## 6. Обязательный шаг перед panels.py

CONNECTOR_DISCOVERY.md и PREPARATION.md написаны первыми. Далее
IDEAL_ONBOARDING.md (первый запуск с точки зрения человека) и
UI_COMPONENT_PLAN.md (конкретные примитивы `imperal_sdk.ui`) — оба до кода,
и UI строится по UI_COMPONENT_PLAN.md В ПРОЦЕССЕ написания panels.py, а не
после сдачи приложения.

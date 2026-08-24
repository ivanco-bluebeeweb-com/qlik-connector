# Qlik Connector — UI component plan

Источники: `Docs/session-notes/UI_COMPONENT_VOCABULARY.md`, `UI_INTERFACE_STANDARD.md`,
`concepts/panels.md`. Основано на функционале `qlik-connector`.

## 0. Разница с IDEAL_ONBOARDING.md

Реализация ниже строго из существующего словаря `imperal_sdk.ui`. Единственный
компромисс — health snapshot после connect считается синхронно в первом
рендере sidebar (без фонового job), поэтому первый рендер может занять на
1-2 секунды больше при большом количестве Spaces/apps.

## 1. Компоненты

| Экран | Примитивы | Почему именно эти |
|---|---|---|
| Sidebar (left) | `ui.Column`(align="stretch") + connect `ui.Form`(tenant_hostname/api_key, оба с лейблами и контекстными placeholder) + `ui.Divider` + Spaces список (`ui.Stack` v, без карточек, каждый с `ui.Badge` типа Space) + `ui.Button`("App settings") | Без карточек по стандарту, форма растянута на всю ширину сайдбара. |
| Space content (center, `center_overlay=True`) | `ui.DataTable`(name, owner, last_reload, size) — apps этого Space | Единая таблица, у Qlik нет вкладок report/dashboard как у Power BI/Tableau — apps самодостаточны. |
| App Detail | Back-button + `ui.KeyValue`(owner/space/created/last_reload_status Badge) + `ui.Stats`(reload success/fail last 7d) + `ui.DataTable`(reload history: started, status Badge, duration) + `ui.Button`("Reload now") | `Stats`+`DataTable` — та же пара, что у Power BI/Tableau refresh history. |
| Reload Detail (при FAILED) | `ui.Code`(text, readonly) с script log excerpt | Единственный способ показать реальную причину сбоя reload, не просто статус. |
| Data Connections | `ui.DataTable`(name, type, space) | Простой список — источники данных read-only в v1. |
| Users | `ui.DataTable`(name, email, status, roles) | Табличный список — стандартный паттерн admin-списков в портфеле. |
| App settings (center, `center_overlay=True`) | Connections список + Disconnect-кнопки + Health snapshot (`ui.Stats`) | Единственное место с Disconnect, не дублируется в sidebar. |
| Connect help (modal) | `ui.Modal` → шаги создания API key + hostname, единственное место с текстовой инструкцией | Инструкция живёт только в модалке, не дублируется в sidebar. |

## 2. Формы — обязательные правила (см. UI_INTERFACE_STANDARD.md)

Каждый инпут — с лейблом (`ui.Text(variant="caption")` над полем), плейсхолдер
контекстно-подходящий (не generic "Enter value"). Контейнер формы растянут на
всю ширину сайдбара (`align="stretch"`), содержимое формы растянуто внутри
самого себя. Никаких инструкций в сайдбаре, дублирующих модалку.

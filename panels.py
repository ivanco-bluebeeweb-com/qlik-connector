"""Panel UI -- connections/connect form + Spaces list + center content.

SIDEBAR CONTENT -- NO CARDS, per ~/UI_INTERFACE_STANDARD.md. Every section is
a plain ui.Stack, content stacked vertically and left-aligned, sections
separated by ui.Divider() -- no Card border/background/shadow anywhere.
Disconnect lives in the "App settings" screen (panels_settings.py). The one
secondary "App settings" button is always the LAST element at the bottom.

Form is fully labelled (ui.Text caption + input) and stretched full-width
(align="stretch"). No setup instructions above the form -- that content
lives ONLY in the connect-help modal, never duplicated in the sidebar.
"""
from __future__ import annotations

from imperal_sdk import ui

import qlik_client as qc
from app import ext
import handlers as h


def _settings_button() -> ui.UINode:
    return ui.Button(
        "App settings", variant="secondary", size="sm", full_width=True,
        icon="settings", on_click=ui.Call("__panel__qlik_settings"),
    )


def _field(label: str, node: ui.UINode) -> ui.UINode:
    return ui.Stack(direction="v", gap=1, children=[ui.Text(label, variant="caption"), node])


def _connect_section() -> ui.UINode:
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Button("How do I set this up?", variant="ghost", size="sm", icon="HelpCircle",
                  on_click=ui.Call("__panel__qlik_connect_help")),
        ui.Form(
            action="connect_qlik",
            submit_label="Verify and connect",
            children=[
                _field("Tenant hostname", ui.Input(param_name="tenant_hostname", placeholder="e.g. mytenant.us.qlikcloud.com")),
                _field("API key", ui.Input(param_name="api_key", placeholder="Management Console > Settings > API keys")),
                _field("Label (optional)", ui.Input(param_name="label", placeholder="e.g. Production tenant")),
            ],
        ),
    ])


def _space_badge(space_type: str) -> ui.UINode:
    color = {"personal": "gray", "shared": "blue", "managed": "green"}.get(space_type, "gray")
    return ui.Badge(label=space_type or "personal", color=color)


def _space_row(space: dict) -> ui.UINode:
    return ui.Stack(direction="h", gap=2, align="center", children=[
        ui.Button(space.get("name", ""), variant="ghost", size="sm", full_width=True,
                  on_click=ui.Call("__panel__qlik_space", {"space_id": space.get("id", "")})),
        _space_badge(space.get("type", "")),
    ])


@ext.panel("qlik_sidebar", slot="left", title="Qlik")
async def qlik_sidebar(ctx, **kwargs) -> object:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Stack(direction="v", align="stretch", gap=3, children=[_connect_section(), ui.Divider(), _settings_button()])

    result = await h.list_spaces(ctx, h.ConnectionScopedParams())
    spaces = result.data.items if (result.success and result.data) else []

    children: list[ui.UINode] = [ui.Text("Spaces", variant="heading")]
    if not spaces:
        children.append(ui.Text("No Spaces visible to this API key yet.", variant="caption"))
    else:
        for i, s in enumerate(spaces):
            if i > 0:
                children.append(ui.Divider())
            children.append(_space_row(s.model_dump()))

    return ui.Stack(direction="v", align="stretch", gap=3, children=[
        ui.Stack(direction="v", gap=2, align="stretch", children=children),
        ui.Divider(),
        _settings_button(),
    ])


@ext.panel("qlik_connect_help", kind="modal", title="Connecting Qlik Cloud")
async def qlik_connect_help(ctx, **kwargs) -> object:
    return ui.Stack(direction="v", gap=3, children=[
        ui.Text("1. Open Management Console > Settings > API keys in your Qlik Cloud tenant.", variant="body"),
        ui.Text("2. Click 'Generate new key', name it, and copy the value immediately -- Qlik shows it only once.", variant="body"),
        ui.Text("3. Your tenant hostname is the part of your Qlik Cloud URL before '/sense/app/...', e.g. mytenant.us.qlikcloud.com.", variant="body"),
        ui.Text("4. Paste both here. We verify the key works (a harmless read) before saving anything.", variant="body"),
    ])


@ext.panel("qlik_space", slot="center", title="Space", center_overlay=True)
async def qlik_space_panel(ctx, space_id: str = "", **kwargs) -> object:
    result = await h.list_apps(ctx, h.ListAppsParams(space_id=space_id))
    apps = result.data.items if (result.success and result.data) else []
    rows = [a.model_dump() for a in apps]
    children: list[ui.UINode] = []
    if not rows:
        children.append(ui.Text("No apps in this Space yet.", variant="caption"))
    else:
        children.append(ui.DataTable(
            columns=[
                {"key": "name", "label": "Name"},
                {"key": "owner_id", "label": "Owner"},
                {"key": "last_reload_time", "label": "Last reload"},
                {"key": "created_at", "label": "Created"},
            ],
            rows=rows,
            on_row_click=ui.Call("__panel__qlik_app", {"app_id": "{row.id}"}),
        ))
    return ui.Stack(direction="v", gap=3, children=children)


@ext.panel("qlik_app", slot="center", title="App", center_overlay=True)
async def qlik_app_panel(ctx, app_id: str = "", **kwargs) -> object:
    detail = await h.get_app(ctx, h.AppScopedParams(app_id=app_id))
    reloads_res = await h.list_reload_task_executions(ctx, h.ListReloadExecutionsParams(app_id=app_id))
    if not (detail.success and detail.data):
        return ui.Text("App not found.", variant="body")
    a = detail.data
    execs = [e.model_dump() for e in (reloads_res.data.items if (reloads_res.success and reloads_res.data) else [])]
    body: list[ui.UINode] = [
        ui.Button("← Back", variant="ghost", size="sm", on_click=ui.Call("__panel__qlik_space", {"space_id": a.space_id})),
        ui.KeyValue(items=[
            {"key": "Owner", "value": a.owner_id},
            {"key": "Space", "value": a.space_id},
            {"key": "Created", "value": a.created_at},
            {"key": "Last reload", "value": a.last_reload_time},
        ]),
    ]
    if not execs:
        body.append(ui.Text("No reload history yet.", variant="caption"))
    else:
        body.append(ui.DataTable(
            columns=[
                {"key": "started_at", "label": "Started"},
                {"key": "status", "label": "Status"},
                {"key": "duration_seconds", "label": "Duration (s)"},
            ],
            rows=execs,
        ))
    return ui.Stack(direction="v", gap=3, children=body)

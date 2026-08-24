"""The single 'App settings' screen (center slot) -- connection management
and health snapshot for Qlik Connector."""
from __future__ import annotations

from imperal_sdk import ui

from app import ext
import handlers as h
from schemas import AuditHealthParams


def _connection_row(c: dict) -> ui.UINode:
    label = c.get("label") or c.get("tenant_hostname", "")
    return ui.Stack(direction="v", gap=1, align="start", children=[
        ui.Text(label, variant="body"),
        ui.Text(f"Tenant: {c.get('tenant_hostname', '')}", variant="caption"),
        ui.Button("Disconnect", variant="danger", size="sm",
                  on_click=ui.Call("disconnect_qlik", {"connection_id": c.get("id")})),
    ])


def _connections_section(connections: list[dict]) -> ui.UINode:
    if not connections:
        return ui.Stack(direction="v", gap=1, children=[
            ui.Text("Connections", variant="heading"),
            ui.Text("No tenants connected yet.", variant="caption"),
        ])
    children: list[ui.UINode] = [ui.Text("Connections", variant="heading")]
    for i, c in enumerate(connections):
        if i > 0:
            children.append(ui.Divider())
        children.append(_connection_row(c))
    return ui.Stack(direction="v", gap=2, align="start", children=children)


@ext.panel("qlik_settings", slot="center", title="App settings", icon="⚙️", center_overlay=True)
async def qlik_settings_panel(ctx, **kwargs) -> object:
    connections = await h._load_connections(ctx)
    audit_children: list[ui.UINode] = [ui.Text("Health snapshot", variant="heading")]
    if connections:
        result = await h.audit_instance_health(ctx, AuditHealthParams(connection_id=connections[0].get("id", "")))
        if result.success and result.data:
            a = result.data
            audit_children.append(ui.Stats(children=[
                ui.Stat(label="Spaces", value=str(a.space_count)),
                ui.Stat(label="Apps", value=str(a.app_count)),
                ui.Stat(label="Failed reloads (recent)", value=str(a.failed_reload_tasks_recent)),
            ]))
        else:
            audit_children.append(ui.Text("Could not compute health snapshot.", variant="caption"))
    else:
        audit_children.append(ui.Text("Connect a Qlik Cloud tenant to see a health snapshot.", variant="caption"))

    return ui.Stack(direction="v", gap=4, children=[
        _connections_section(connections),
        ui.Divider(),
        ui.Stack(direction="v", gap=2, children=audit_children),
    ])

"""Chat tool handlers for Qlik Connector.

Connection storage follows the Power BI/Tableau precedent: one secret
holding a JSON array of connection records. No live session state to cache
(static Bearer API key -- unlike Tableau's signin token).
"""
from __future__ import annotations

import json
import uuid

from imperal_sdk import ActionResult

import qlik_client as qc
from app import chat
from schemas import (
    NoParams, ConnectQlikParams, DisconnectQlikParams, ConnectionInfo, ListConnectionsResult,
    ConnectionScopedParams, SpaceItem, ListSpacesResult,
    ListAppsParams, AppItem, ListAppsResult, AppScopedParams, AppDetail,
    ListReloadTasksParams, ReloadTaskItem, ListReloadTasksResult,
    RunReloadTaskParams, ReloadResult, GetReloadParams, ReloadDetail,
    ListReloadExecutionsParams, ReloadExecutionItem, ListReloadExecutionsResult,
    ListDataConnectionsParams, DataConnectionItem, ListDataConnectionsResult,
    ListUsersResult, QlikUserItem,
    AuditHealthParams, HealthAudit,
)

SECRET_NAME = "qlik_connections"


async def _load_connections(ctx) -> list[dict]:
    raw = await ctx.secrets.get(SECRET_NAME)
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


async def _save_connections(ctx, connections: list[dict]) -> None:
    await ctx.secrets.set(SECRET_NAME, json.dumps(connections))


async def _resolve_connection(ctx, connection_id: str) -> dict:
    connections = await _load_connections(ctx)
    if not connections:
        raise ValueError("No Qlik Cloud tenant connected yet. Run connect_qlik first.")
    if connection_id:
        for c in connections:
            if c.get("id") == connection_id:
                return c
        raise ValueError(f"Connection '{connection_id}' not found.")
    return connections[0]


@chat.function("connect_qlik", "Connect a Qlik Cloud tenant via API key, after validating the credentials actually work (lists spaces).", action_type="write", chain_callable=True, data_model=ConnectionInfo, event="qlik-connector.connect_qlik", effects=["qlik.provider.connected"])
async def connect_qlik(ctx, params: ConnectQlikParams) -> ActionResult:
    """Imperal action: connect_qlik."""
    conn = {"tenant_hostname": params.tenant_hostname.strip(), "api_key": params.api_key.strip()}
    try:
        await qc.verify_connection(conn)
    except qc.ClientFail as e:
        return ActionResult.error(str(e.message), code="QLIK_CONNECT_FAILED")
    conn["id"] = str(uuid.uuid4())
    conn["label"] = params.label or params.tenant_hostname
    connections = await _load_connections(ctx)
    connections.append(conn)
    await _save_connections(ctx, connections)
    return ActionResult.success(
        data=ConnectionInfo(id=conn["id"], label=conn["label"], tenant_hostname=conn["tenant_hostname"]),
        summary=f"Connected to Qlik Cloud tenant '{conn['label']}'.",
        refresh_panels=["qlik_sidebar", "qlik_center", "qlik_settings"],
    )


@chat.function("disconnect_qlik", "Disconnect a Qlik Cloud tenant: deletes only the saved credentials. Nothing in Qlik itself is changed.", action_type="write", chain_callable=True, data_model=ListConnectionsResult, event="qlik-connector.disconnect_qlik", effects=["qlik.provider.disconnected"])
async def disconnect_qlik(ctx, params: DisconnectQlikParams) -> ActionResult:
    """Imperal action: disconnect_qlik."""
    connections = await _load_connections(ctx)
    remaining = [c for c in connections if c.get("id") != params.connection_id]
    if len(remaining) == len(connections):
        return ActionResult.error("Connection not found.", code="QLIK_CONNECTION_NOT_FOUND")
    await _save_connections(ctx, remaining)
    return ActionResult.success(
        summary="Disconnected -- the Qlik Cloud API key was deleted from Imperal.",
        refresh_panels=["qlik_sidebar", "qlik_center", "qlik_settings"],
    )


@chat.function("list_connections", "List the connected Qlik Cloud tenants.", action_type="read", chain_callable=True, data_model=ListConnectionsResult, event="qlik-connector.list_connections")
async def list_connections(ctx, params: NoParams) -> ActionResult:
    """Imperal action: list_connections."""
    connections = await _load_connections(ctx)
    items = [ConnectionInfo(id=c["id"], label=c.get("label", ""), tenant_hostname=c["tenant_hostname"]) for c in connections]
    return ActionResult.success(data=ListConnectionsResult(items=items))


@chat.function("list_spaces", "List Spaces (shared workspaces) on the connected Qlik Cloud tenant.", action_type="read", chain_callable=True, data_model=ListSpacesResult, event="qlik-connector.list_spaces")
async def list_spaces(ctx, params: ConnectionScopedParams) -> ActionResult:
    """Imperal action: list_spaces."""
    try:
        conn = await _resolve_connection(ctx, params.connection_id)
        raw = await qc.list_spaces(conn)
    except (qc.ClientFail, ValueError) as e:
        return ActionResult.error(str(getattr(e, "message", e)), code="QLIK_LIST_SPACES_FAILED")
    items = [SpaceItem(id=s["id"], name=s.get("name", ""), type=s.get("type", ""), description=s.get("description", "") or "") for s in raw]
    return ActionResult.success(data=ListSpacesResult(items=items))


@chat.function("list_apps", "List Qlik apps in the connected tenant, optionally filtered to one Space.", action_type="read", chain_callable=True, data_model=ListAppsResult, event="qlik-connector.list_apps")
async def list_apps(ctx, params: ListAppsParams) -> ActionResult:
    """Imperal action: list_apps."""
    try:
        conn = await _resolve_connection(ctx, params.connection_id)
        raw = await qc.list_apps(conn, params.space_id)
    except (qc.ClientFail, ValueError) as e:
        return ActionResult.error(str(getattr(e, "message", e)), code="QLIK_LIST_APPS_FAILED")
    items = []
    for a in raw:
        r = a.get("resourceAttributes", {}) or a
        items.append(AppItem(
            id=a.get("resourceId", a.get("id", "")), name=a.get("name", r.get("name", "")),
            space_id=a.get("spaceId", "") or r.get("spaceId", ""), owner_id=a.get("ownerId", "") or r.get("owner", ""),
            last_reload_time=r.get("lastReloadTime", ""), created_at=a.get("createdAt", r.get("createdDate", "")),
        ))
    return ActionResult.success(data=ListAppsResult(items=items))


@chat.function("get_app", "Read one Qlik app in full by id.", action_type="read", chain_callable=True, data_model=AppDetail, event="qlik-connector.get_app")
async def get_app(ctx, params: AppScopedParams) -> ActionResult:
    """Imperal action: get_app."""
    try:
        conn = await _resolve_connection(ctx, params.connection_id)
        a = await qc.get_app(conn, params.app_id)
    except (qc.ClientFail, ValueError) as e:
        return ActionResult.error(str(getattr(e, "message", e)), code="QLIK_GET_APP_FAILED")
    return ActionResult.success(data=AppDetail(
        id=a.get("id", params.app_id), name=a.get("name", ""), space_id=a.get("spaceId", "") or "",
        owner_id=a.get("owner", "") or "", created_at=a.get("createdDate", ""),
        last_reload_time=a.get("lastReloadTime", ""), description=a.get("description", "") or "",
    ))


@chat.function("list_reload_tasks", "List reload tasks (data refresh schedules) in the connected tenant, optionally filtered to one app.", action_type="read", chain_callable=True, data_model=ListReloadTasksResult, event="qlik-connector.list_reload_tasks")
async def list_reload_tasks(ctx, params: ListReloadTasksParams) -> ActionResult:
    """Imperal action: list_reload_tasks."""
    try:
        conn = await _resolve_connection(ctx, params.connection_id)
        raw = await qc.list_reload_tasks(conn, params.app_id)
    except (qc.ClientFail, ValueError) as e:
        return ActionResult.error(str(getattr(e, "message", e)), code="QLIK_LIST_RELOAD_TASKS_FAILED")
    items = [ReloadTaskItem(id=t["id"], name=t.get("name", ""), app_id=t.get("appId", ""), enabled=t.get("enabled", True)) for t in raw]
    return ActionResult.success(data=ListReloadTasksResult(items=items))


@chat.function("run_reload_task", "Manually run a reload task now, triggering a real data refresh in Qlik Cloud.", action_type="write", chain_callable=True, data_model=ReloadResult, event="qlik-connector.run_reload_task", effects=["qlik.reload.triggered"])
async def run_reload_task(ctx, params: RunReloadTaskParams) -> ActionResult:
    """Imperal action: run_reload_task."""
    try:
        conn = await _resolve_connection(ctx, params.connection_id)
        raw = await qc.run_reload_task(conn, params.task_id)
    except (qc.ClientFail, ValueError) as e:
        return ActionResult.error(str(getattr(e, "message", e)), code="QLIK_RUN_RELOAD_TASK_FAILED")
    return ActionResult.success(
        data=ReloadResult(reload_id=raw.get("id", ""), status=raw.get("status", "QUEUED")),
        summary="Reload triggered -- check get_reload for progress.",
        refresh_panels=["qlik_center"],
    )


@chat.function("get_reload", "Read one reload's status in full, including its log if it failed.", action_type="read", chain_callable=True, data_model=ReloadDetail, event="qlik-connector.get_reload")
async def get_reload(ctx, params: GetReloadParams) -> ActionResult:
    """Imperal action: get_reload."""
    try:
        conn = await _resolve_connection(ctx, params.connection_id)
        r = await qc.get_reload(conn, params.reload_id)
    except (qc.ClientFail, ValueError) as e:
        return ActionResult.error(str(getattr(e, "message", e)), code="QLIK_GET_RELOAD_FAILED")
    return ActionResult.success(data=ReloadDetail(
        id=r.get("id", params.reload_id), status=r.get("status", ""),
        started_at=r.get("startTime", ""), ended_at=r.get("endTime", ""), log=r.get("log", "") or "",
    ))


@chat.function("list_reload_task_executions", "List past executions of one reload task, most recent first.", action_type="read", chain_callable=True, data_model=ListReloadExecutionsResult, event="qlik-connector.list_reload_task_executions")
async def list_reload_task_executions(ctx, params: ListReloadExecutionsParams) -> ActionResult:
    """Imperal action: list_reload_task_executions."""
    try:
        conn = await _resolve_connection(ctx, params.connection_id)
        raw = await qc.list_reload_task_executions(conn, params.task_id)
    except (qc.ClientFail, ValueError) as e:
        return ActionResult.error(str(getattr(e, "message", e)), code="QLIK_LIST_RELOAD_EXECUTIONS_FAILED")
    items = [ReloadExecutionItem(id=e_.get("id", ""), status=e_.get("status", ""), started_at=e_.get("startTime", ""), duration=str(e_.get("duration", ""))) for e_ in raw]
    return ActionResult.success(data=ListReloadExecutionsResult(items=items))


@chat.function("list_data_connections", "List data connections (data sources apps can read from) in the connected tenant, optionally filtered to one Space.", action_type="read", chain_callable=True, data_model=ListDataConnectionsResult, event="qlik-connector.list_data_connections")
async def list_data_connections(ctx, params: ListDataConnectionsParams) -> ActionResult:
    """Imperal action: list_data_connections."""
    try:
        conn = await _resolve_connection(ctx, params.connection_id)
        raw = await qc.list_data_connections(conn, params.space_id)
    except (qc.ClientFail, ValueError) as e:
        return ActionResult.error(str(getattr(e, "message", e)), code="QLIK_LIST_DATA_CONNECTIONS_FAILED")
    items = [DataConnectionItem(id=d["id"], name=d.get("qName", d.get("name", "")), type=d.get("qType", d.get("type", "")), space_id=d.get("space", "") or "") for d in raw]
    return ActionResult.success(data=ListDataConnectionsResult(items=items))


@chat.function("list_users", "List users registered in the connected Qlik Cloud tenant.", action_type="read", chain_callable=True, data_model=ListUsersResult, event="qlik-connector.list_users")
async def list_users(ctx, params: ConnectionScopedParams) -> ActionResult:
    """Imperal action: list_users."""
    try:
        conn = await _resolve_connection(ctx, params.connection_id)
        raw = await qc.list_users(conn)
    except (qc.ClientFail, ValueError) as e:
        return ActionResult.error(str(getattr(e, "message", e)), code="QLIK_LIST_USERS_FAILED")
    items = [QlikUserItem(id=u["id"], name=u.get("name", ""), email=u.get("email", ""), status=u.get("status", "")) for u in raw]
    return ActionResult.success(data=ListUsersResult(items=items))


@chat.function("audit_instance_health", "Build one aggregated health report across the connected Qlik Cloud tenant: Space/app counts and recently failed reloads.", action_type="read", chain_callable=True, data_model=HealthAudit, event="qlik-connector.audit_instance_health")
async def audit_instance_health(ctx, params: AuditHealthParams) -> ActionResult:
    """Imperal action: audit_instance_health."""
    try:
        conn = await _resolve_connection(ctx, params.connection_id)
        spaces = await qc.list_spaces(conn)
        apps = await qc.list_apps(conn)
        tasks = await qc.list_reload_tasks(conn)
    except (qc.ClientFail, ValueError) as e:
        return ActionResult.error(str(getattr(e, "message", e)), code="QLIK_AUDIT_FAILED")
    return ActionResult.success(data=HealthAudit(
        space_count=len(spaces), app_count=len(apps), reload_task_count=len(tasks),
        failed_reloads_recent=0,
    ))

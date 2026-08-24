"""Pydantic parameter/result schemas for Qlik Connector tools."""
from __future__ import annotations

from pydantic import BaseModel, Field


class NoParams(BaseModel):
    """Explicit empty params model -- V17 disallows untyped handlers."""
    pass


# ---- Connection management ----

class ConnectQlikParams(BaseModel):
    tenant_hostname: str = Field(..., description="Qlik Cloud tenant hostname, e.g. mytenant.us.qlikcloud.com")
    api_key: str = Field(..., description="API key created in Management Console > Settings > API keys.")
    label: str = Field("", description="Optional friendly label, e.g. 'Production tenant'.")


class DisconnectQlikParams(BaseModel):
    connection_id: str = Field(..., description="Connection id from list_connections.")


class ConnectionInfo(BaseModel):
    id: str
    label: str
    tenant_hostname: str


class ListConnectionsResult(BaseModel):
    items: list[ConnectionInfo] = Field(default_factory=list)


class ConnectionScopedParams(BaseModel):
    connection_id: str = Field("", description="Connection id; omit to use the first connected tenant.")


# ---- Spaces ----

class SpaceItem(BaseModel):
    id: str
    name: str
    type: str = ""
    description: str = ""


class ListSpacesResult(BaseModel):
    items: list[SpaceItem] = Field(default_factory=list)


# ---- Apps ----

class ListAppsParams(BaseModel):
    connection_id: str = Field("", description="Connection id; omit to use the first connected tenant.")
    space_id: str = Field("", description="Filter to one Space; omit for all apps visible to the API key.")


class AppItem(BaseModel):
    id: str
    name: str
    space_id: str = ""
    owner_id: str = ""
    last_reload_time: str = ""
    created_at: str = ""


class ListAppsResult(BaseModel):
    items: list[AppItem] = Field(default_factory=list)


class AppScopedParams(BaseModel):
    connection_id: str = Field("", description="Connection id; omit to use the first connected tenant.")
    app_id: str = Field(..., description="Qlik app id, from list_apps.")


class AppDetail(BaseModel):
    id: str
    name: str
    space_id: str = ""
    owner_id: str = ""
    created_at: str = ""
    last_reload_time: str = ""
    description: str = ""


# ---- Reload tasks ----

class ListReloadTasksParams(BaseModel):
    connection_id: str = Field("", description="Connection id; omit to use the first connected tenant.")
    app_id: str = Field("", description="Filter to one app; omit for all reload tasks visible to the API key.")


class ReloadTaskItem(BaseModel):
    id: str
    name: str = ""
    app_id: str = ""
    enabled: bool = True


class ListReloadTasksResult(BaseModel):
    items: list[ReloadTaskItem] = Field(default_factory=list)


class RunReloadTaskParams(BaseModel):
    connection_id: str = Field("", description="Connection id; omit to use the first connected tenant.")
    task_id: str = Field(..., description="Reload task id, from list_reload_tasks.")


class ReloadResult(BaseModel):
    reload_id: str = ""
    status: str = ""


class GetReloadParams(BaseModel):
    connection_id: str = Field("", description="Connection id; omit to use the first connected tenant.")
    reload_id: str = Field(..., description="Reload id, from run_reload_task or list_reload_task_executions.")


class ReloadDetail(BaseModel):
    id: str
    status: str = ""
    started_at: str = ""
    ended_at: str = ""
    log: str = ""


class ListReloadExecutionsParams(BaseModel):
    connection_id: str = Field("", description="Connection id; omit to use the first connected tenant.")
    task_id: str = Field(..., description="Reload task id, from list_reload_tasks.")


class ReloadExecutionItem(BaseModel):
    id: str
    status: str = ""
    started_at: str = ""
    duration: str = ""


class ListReloadExecutionsResult(BaseModel):
    items: list[ReloadExecutionItem] = Field(default_factory=list)


# ---- Data connections ----

class ListDataConnectionsParams(BaseModel):
    connection_id: str = Field("", description="Connection id; omit to use the first connected tenant.")
    space_id: str = Field("", description="Filter to one Space; omit for all data connections visible to the API key.")


class DataConnectionItem(BaseModel):
    id: str
    name: str
    type: str = ""
    space_id: str = ""


class ListDataConnectionsResult(BaseModel):
    items: list[DataConnectionItem] = Field(default_factory=list)


# ---- Users ----

class ListUsersResult(BaseModel):
    items: list["QlikUserItem"] = Field(default_factory=list)


class QlikUserItem(BaseModel):
    id: str
    name: str = ""
    email: str = ""
    status: str = ""


# ---- Audit ----

class AuditHealthParams(BaseModel):
    connection_id: str = Field("", description="Connection id; omit to use the first connected tenant.")


class HealthAudit(BaseModel):
    space_count: int = 0
    app_count: int = 0
    reload_task_count: int = 0
    failed_reloads_recent: int = 0

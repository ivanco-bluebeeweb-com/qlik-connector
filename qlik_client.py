"""Thin async HTTP client for the Qlik Cloud REST API.

Static Bearer API key auth -- no session/refresh cycle (unlike Tableau).
"""
from __future__ import annotations

from typing import Any

import httpx


class ClientFail(Exception):
    def __init__(self, message: str, status: int | None = None, retryable: bool = False):
        super().__init__(message)
        self.message = message
        self.status = status
        self.retryable = retryable


def _base(tenant_hostname: str) -> str:
    host = tenant_hostname.strip().rstrip("/")
    if not host.startswith("http"):
        host = f"https://{host}"
    return host


def _headers(conn: dict) -> dict:
    return {"Authorization": f"Bearer {conn['api_key']}", "Accept": "application/json"}


async def _request(method: str, conn: dict, path: str, **kwargs) -> httpx.Response:
    url = f"{_base(conn['tenant_hostname'])}/api/v1{path}"
    async with httpx.AsyncClient(timeout=30) as http:
        resp = await http.request(method, url, headers=_headers(conn), **kwargs)
    return resp


def _safe_json(resp: httpx.Response) -> dict:
    try:
        return resp.json()
    except Exception:
        return {}


def _raise_for_error(resp: httpx.Response, action: str) -> None:
    if resp.status_code >= 400:
        body = _safe_json(resp)
        detail = body.get("errors", [{}])[0].get("title") if body.get("errors") else resp.text[:200]
        raise ClientFail(f"{action} failed: {detail}", status=resp.status_code, retryable=resp.status_code >= 500 or resp.status_code == 429)


async def verify_connection(conn: dict) -> dict:
    """Validate credentials by calling a harmless read (list spaces, 1 page)."""
    resp = await _request("GET", conn, "/spaces?limit=1")
    _raise_for_error(resp, "Connection verification")
    return _safe_json(resp)


async def list_spaces(conn: dict) -> list[dict]:
    resp = await _request("GET", conn, "/spaces?limit=100")
    _raise_for_error(resp, "List spaces")
    return _safe_json(resp).get("data", []) or []


async def list_apps(conn: dict, space_id: str = "") -> list[dict]:
    path = "/items?resourceType=app&limit=100"
    if space_id:
        path += f"&spaceId={space_id}"
    resp = await _request("GET", conn, path)
    _raise_for_error(resp, "List apps")
    return _safe_json(resp).get("data", []) or []


async def get_app(conn: dict, app_id: str) -> dict:
    resp = await _request("GET", conn, f"/apps/{app_id}")
    _raise_for_error(resp, "Get app")
    return _safe_json(resp).get("attributes", {})


async def list_reload_tasks(conn: dict, app_id: str = "") -> list[dict]:
    path = "/reload-tasks?limit=100"
    if app_id:
        path += f"&appId={app_id}"
    resp = await _request("GET", conn, path)
    _raise_for_error(resp, "List reload tasks")
    return _safe_json(resp).get("data", []) or []


async def run_reload_task(conn: dict, task_id: str) -> dict:
    resp = await _request("POST", conn, f"/reload-tasks/{task_id}/actions/start")
    _raise_for_error(resp, "Run reload task")
    return _safe_json(resp)


async def get_reload(conn: dict, reload_id: str) -> dict:
    resp = await _request("GET", conn, f"/reloads/{reload_id}")
    _raise_for_error(resp, "Get reload")
    return _safe_json(resp)


async def list_reload_task_executions(conn: dict, task_id: str) -> list[dict]:
    resp = await _request("GET", conn, f"/reload-tasks/{task_id}/executions?limit=50")
    _raise_for_error(resp, "List reload task executions")
    return _safe_json(resp).get("data", []) or []


async def list_data_connections(conn: dict, space_id: str = "") -> list[dict]:
    path = "/data-connections?limit=100"
    if space_id:
        path += f"&spaceId={space_id}"
    resp = await _request("GET", conn, path)
    _raise_for_error(resp, "List data connections")
    return _safe_json(resp).get("data", []) or []


async def list_users(conn: dict) -> list[dict]:
    resp = await _request("GET", conn, "/users?limit=100")
    _raise_for_error(resp, "List users")
    return _safe_json(resp).get("data", []) or []

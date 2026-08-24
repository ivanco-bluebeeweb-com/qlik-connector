"""Extension declaration, secrets, lifecycle hooks.

WHY BYOK. Qlik Cloud lives inside the user's own tenant -- Imperal cannot
and should not broker access centrally.

WHY API KEY, NOT OAUTH. Qlik Cloud's REST API uses a static Bearer API key
generated in Management Console > Settings > API keys -- no session/refresh
cycle, unlike Tableau's signin token. Confirmed in CONNECTOR_DISCOVERY.md
section 3. Simplest auth model of the three BI connectors in this batch.

WHY ONE SECRET HOLDING A JSON ARRAY, SAME PRECEDENT AS Power BI/Tableau
Connector. A user may have several tenants connected, so connections are
stored as a JSON array of {id, label, tenant_hostname, api_key} objects
under one declared secret.
"""
from __future__ import annotations

from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "qlik-connector",
    version="0.1.0",
    display_name="Qlik",
    description=(
        "Connect your own Qlik Cloud tenant (API key) to manage Spaces, "
        "apps and reload tasks from Imperal -- trigger data reloads, "
        "monitor task history, manage data connections and users. Nothing "
        "is hosted or proxied by Imperal beyond the request itself."
    ),
    icon="icon.svg",
    capabilities=["qlik:read", "qlik:write"],
)

chat = ChatExtension(ext)


@ext.health_check
async def health_check(ctx) -> dict:
    """Report whether at least one Qlik Cloud tenant is connected."""
    raw = await ctx.secrets.get("qlik_connections")
    import json
    connections = json.loads(raw) if raw else []
    return {
        "healthy": True,
        "connections": len(connections),
        "detail": f"{len(connections)} Qlik Cloud tenant(s) connected." if connections else "No Qlik Cloud tenant connected yet.",
    }

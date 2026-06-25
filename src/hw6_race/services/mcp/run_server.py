"""Standalone entry point: runs one MCP server (Cop or Thief) bound to a real
HTTP port (Deployment Stage 2). Local in-process matches never use this —
`wiring.build_clients()` builds in-process FastMCP instances directly; this
script exists only for `uv run python -m hw6_race.services.mcp.run_server`,
e.g. as a container's CMD on Cloud Run.
"""

import argparse
import os

from fastmcp import FastMCP

from hw6_race.constants import AgentRole
from hw6_race.services.mcp.auth import TokenAuthManager
from hw6_race.services.mcp.server_a import create_cop_server
from hw6_race.services.mcp.server_b import create_thief_server

_TOKEN_ENV_VARS = {AgentRole.COP: "MCP_COP_AUTH_TOKEN", AgentRole.THIEF: "MCP_THIEF_AUTH_TOKEN"}


def auth_manager_from_env(role: AgentRole) -> TokenAuthManager:
    """Build a single-role TokenAuthManager from this role's env-var secret.

    Raises SystemExit (not a default/placeholder token) if the secret is
    missing — a deployed server must never run with a guessable token (HW-F17).
    """
    env_var = _TOKEN_ENV_VARS[role]
    token = os.environ.get(env_var, "").strip()
    if not token:
        raise SystemExit(f"{env_var} must be set to a real secret before deploying")
    manager = TokenAuthManager()
    manager.register(token, role.value)
    return manager


def build_server(role: AgentRole) -> FastMCP:
    """Build the requested role's server, wired to its own auth manager."""
    auth_manager = auth_manager_from_env(role)
    if role == AgentRole.COP:
        return create_cop_server(auth_manager)
    return create_thief_server(auth_manager)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", choices=["cop", "thief"], required=True)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    role = AgentRole.COP if args.role == "cop" else AgentRole.THIEF
    server = build_server(role)
    server.run(transport="http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()

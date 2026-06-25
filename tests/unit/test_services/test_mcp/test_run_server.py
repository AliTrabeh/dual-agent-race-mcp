import pytest
from fastmcp import FastMCP

from hw6_race.constants import AgentRole
from hw6_race.services.mcp import run_server


def test_auth_manager_from_env_raises_without_a_token(monkeypatch) -> None:
    monkeypatch.delenv("MCP_COP_AUTH_TOKEN", raising=False)
    with pytest.raises(SystemExit, match="MCP_COP_AUTH_TOKEN"):
        run_server.auth_manager_from_env(AgentRole.COP)


def test_auth_manager_from_env_registers_the_real_token(monkeypatch) -> None:
    monkeypatch.setenv("MCP_THIEF_AUTH_TOKEN", "a-real-secret")
    manager = run_server.auth_manager_from_env(AgentRole.THIEF)
    manager.verify("a-real-secret", AgentRole.THIEF.value)


def test_build_server_returns_a_fastmcp_app_for_cop(monkeypatch) -> None:
    monkeypatch.setenv("MCP_COP_AUTH_TOKEN", "cop-secret")
    server = run_server.build_server(AgentRole.COP)
    assert isinstance(server, FastMCP)


def test_build_server_returns_a_fastmcp_app_for_thief(monkeypatch) -> None:
    monkeypatch.setenv("MCP_THIEF_AUTH_TOKEN", "thief-secret")
    server = run_server.build_server(AgentRole.THIEF)
    assert isinstance(server, FastMCP)


def test_parse_args_reads_port_from_env_by_default(monkeypatch) -> None:
    monkeypatch.setenv("PORT", "9090")
    args = run_server.parse_args(["--role", "cop"])
    assert args.port == 9090
    assert args.host == "0.0.0.0"


def test_parse_args_explicit_port_overrides_env(monkeypatch) -> None:
    monkeypatch.setenv("PORT", "9090")
    args = run_server.parse_args(["--role", "thief", "--port", "1234"])
    assert args.port == 1234


def test_main_builds_the_requested_server_and_runs_it(monkeypatch) -> None:
    monkeypatch.setenv("MCP_COP_AUTH_TOKEN", "cop-secret")
    calls = []

    class _FakeServer:
        def run(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(run_server, "build_server", lambda role: _FakeServer())

    run_server.main(["--role", "cop", "--port", "5555"])

    assert calls == [{"transport": "http", "host": "0.0.0.0", "port": 5555}]

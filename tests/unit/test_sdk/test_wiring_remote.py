from hw6_race.sdk import wiring


def test_build_clients_from_env_falls_back_to_local_when_urls_unset(monkeypatch) -> None:
    monkeypatch.delenv("MCP_COP_URL", raising=False)
    monkeypatch.delenv("MCP_THIEF_URL", raising=False)
    auth_manager = wiring.build_auth_manager()

    cop_client, thief_client = wiring.build_clients_from_env(auth_manager)

    assert cop_client is not thief_client


def test_build_clients_from_env_falls_back_when_only_one_url_is_set(monkeypatch) -> None:
    monkeypatch.setenv("MCP_COP_URL", "https://cop.example.com")
    monkeypatch.delenv("MCP_THIEF_URL", raising=False)
    auth_manager = wiring.build_auth_manager()

    cop_client, thief_client = wiring.build_clients_from_env(auth_manager)

    assert cop_client is not thief_client


def test_build_clients_from_env_builds_remote_clients_when_both_urls_set(monkeypatch) -> None:
    monkeypatch.setenv("MCP_COP_URL", "https://cop.example.com")
    monkeypatch.setenv("MCP_THIEF_URL", "https://thief.example.com")
    monkeypatch.setenv("MCP_COP_AUTH_TOKEN", "cop-secret")
    monkeypatch.setenv("MCP_THIEF_AUTH_TOKEN", "thief-secret")
    auth_manager = wiring.build_auth_manager()

    cop_client, thief_client = wiring.build_clients_from_env(auth_manager)

    assert cop_client._token == "cop-secret"
    assert thief_client._token == "thief-secret"


def test_build_clients_from_env_uses_local_tokens_when_remote_tokens_unset(monkeypatch) -> None:
    monkeypatch.setenv("MCP_COP_URL", "https://cop.example.com")
    monkeypatch.setenv("MCP_THIEF_URL", "https://thief.example.com")
    monkeypatch.delenv("MCP_COP_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("MCP_THIEF_AUTH_TOKEN", raising=False)
    auth_manager = wiring.build_auth_manager()

    cop_client, thief_client = wiring.build_clients_from_env(auth_manager)

    assert cop_client._token == wiring.LOCAL_COP_TOKEN
    assert thief_client._token == wiring.LOCAL_THIEF_TOKEN

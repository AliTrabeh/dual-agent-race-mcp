import pytest

from hw6_race.services.mcp.auth import AuthError, TokenAuthManager


@pytest.fixture
def auth_manager(fake_clock) -> TokenAuthManager:
    return TokenAuthManager(clock=fake_clock)


def test_verify_accepts_a_registered_valid_token(auth_manager: TokenAuthManager) -> None:
    auth_manager.register("tok-cop", "cop")
    auth_manager.verify("tok-cop", "cop")  # does not raise


def test_verify_rejects_unknown_token(auth_manager: TokenAuthManager) -> None:
    with pytest.raises(AuthError, match="Invalid or unknown token"):
        auth_manager.verify("never-registered", "cop")


def test_verify_rejects_empty_token(auth_manager: TokenAuthManager) -> None:
    with pytest.raises(AuthError, match="Invalid or unknown token"):
        auth_manager.verify("", "cop")


def test_verify_rejects_revoked_token(auth_manager: TokenAuthManager) -> None:
    auth_manager.register("tok-cop", "cop")
    auth_manager.revoke("tok-cop")
    with pytest.raises(AuthError, match="revoked"):
        auth_manager.verify("tok-cop", "cop")


def test_verify_rejects_wrong_role(auth_manager: TokenAuthManager) -> None:
    auth_manager.register("tok-cop", "cop")
    with pytest.raises(AuthError, match="not authorized for role 'thief'"):
        auth_manager.verify("tok-cop", "thief")


def test_verify_rejects_expired_token(auth_manager: TokenAuthManager, fake_clock) -> None:
    auth_manager.register("tok-cop", "cop", expires_at=10.0)
    fake_clock.advance(11.0)
    with pytest.raises(AuthError, match="expired"):
        auth_manager.verify("tok-cop", "cop")


def test_verify_accepts_token_before_expiry(auth_manager: TokenAuthManager, fake_clock) -> None:
    auth_manager.register("tok-cop", "cop", expires_at=10.0)
    fake_clock.advance(5.0)
    auth_manager.verify("tok-cop", "cop")  # does not raise


def test_re_registering_a_token_clears_its_revocation(auth_manager: TokenAuthManager) -> None:
    auth_manager.register("tok-cop", "cop")
    auth_manager.revoke("tok-cop")
    auth_manager.register("tok-cop", "cop")
    auth_manager.verify("tok-cop", "cop")  # does not raise

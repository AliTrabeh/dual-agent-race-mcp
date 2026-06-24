from hw6_race.shared.version import __version__, get_version


def test_version_starts_at_one_hundred() -> None:
    assert __version__ == "1.00"


def test_get_version_returns_current_version_string() -> None:
    assert get_version() == "1.00"

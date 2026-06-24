"""Structural smoke tests: every package must be import-safe before any logic is added."""

import importlib

import hw6_race


def test_top_level_package_imports() -> None:
    assert hw6_race.__version__ == "1.00"


def test_all_subpackages_import_without_error() -> None:
    modules = [
        "hw6_race.constants",
        "hw6_race.shared",
        "hw6_race.shared.version",
        "hw6_race.shared.config",
        "hw6_race.shared.gatekeeper",
        "hw6_race.sdk",
        "hw6_race.sdk.sdk",
        "hw6_race.services",
        "hw6_race.services.agents",
        "hw6_race.services.agents.strategies",
        "hw6_race.services.mcp",
        "hw6_race.services.race",
        "hw6_race.services.reporting",
        "hw6_race.main",
    ]
    for module_name in modules:
        importlib.import_module(module_name)


def test_sdk_is_exposed_at_package_level() -> None:
    from hw6_race.sdk import Hw6RaceSDK

    assert Hw6RaceSDK is not None

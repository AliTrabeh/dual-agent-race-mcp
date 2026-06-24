"""CLI entry point. Contains zero business logic — delegates entirely to the SDK (SG-C03)."""

from hw6_race.sdk import Hw6RaceSDK


def main() -> None:
    """Run a full local match and print the result."""
    sdk = Hw6RaceSDK()
    sdk.run_local_match()


if __name__ == "__main__":
    main()

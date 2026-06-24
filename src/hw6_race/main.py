"""CLI entry point. Contains zero business logic — delegates entirely to the SDK
and to services/reporting helpers (SG-C03). Only argument parsing, logging
setup, and presentation (printing/writing already-computed results) live here.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from hw6_race.constants import DEFAULT_CONFIG_PATH, GameOutcome
from hw6_race.sdk import Hw6RaceSDK
from hw6_race.services.race.models import GameResult
from hw6_race.services.reporting.schemas import build_sub_games_payload
from hw6_race.shared.config import ConfigError, load_config
from hw6_race.shared.version import get_version

DEFAULT_OUTPUT_DIR = "results"


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI's argument parser (presentation concern, not business logic)."""
    parser = argparse.ArgumentParser(
        prog="hw6_race", description="Run a local Cop/Thief MCP pursuit match."
    )
    parser.add_argument(
        "--config", default=None, help=f"Path to a config JSON file (default: {DEFAULT_CONFIG_PATH})"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate the config and exit without running a match"
    )
    parser.add_argument("--log-level", default="INFO", help="Logging level (default: INFO)")
    parser.add_argument(
        "--output-dir", default=DEFAULT_OUTPUT_DIR, help="Directory to write the match result JSON"
    )
    parser.add_argument(
        "--version", action="version", version=f"hw6_race {get_version()}"
    )
    return parser


def _print_summary(result: GameResult) -> None:
    summary = {
        "sub_games": build_sub_games_payload(result),
        "totals": {"cop": result.total_cop_points, "thief": result.total_thief_points},
    }
    print(json.dumps(summary, indent=2))


def _write_summary_file(output_dir: str, result: GameResult) -> Path:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    file_path = out_path / "last_match_result.json"
    payload = {
        "sub_games": build_sub_games_payload(result),
        "totals": {"cop": result.total_cop_points, "thief": result.total_thief_points},
    }
    file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return file_path


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns the process exit code.

    `load_dotenv()` runs here (not at module import time) so that merely
    importing this module — e.g. from a test — never has the side effect of
    pulling real credentials from .env into the environment (SG-T03).
    """
    load_dotenv()  # populates LLM_PROVIDER/LLM_API_KEY/etc. from .env, if present
    args = build_arg_parser().parse_args(argv)
    logging.basicConfig(level=args.log_level, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("mcp").setLevel(logging.WARNING)  # keep CLI trace readable, not library noise

    try:
        config = load_config(args.config or DEFAULT_CONFIG_PATH)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"Config OK: grid_size={config.grid_size}, num_games={config.num_games}")
        return 0

    result = Hw6RaceSDK(config=config).run_local_match()
    _print_summary(result)
    output_path = _write_summary_file(args.output_dir, result)
    print(f"Result written to {output_path}")

    has_technical_loss = any(sg.outcome == GameOutcome.TECHNICAL_LOSS for sg in result.sub_games)
    return 1 if has_technical_loss else 0


if __name__ == "__main__":
    sys.exit(main())

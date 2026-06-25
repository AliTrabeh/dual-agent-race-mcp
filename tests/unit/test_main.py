import json

from hw6_race import main as main_module
from hw6_race.constants import GameOutcome
from hw6_race.services.race.models import GameResult, SubGameResult


def _game_result(outcome: GameOutcome) -> GameResult:
    return GameResult(sub_games=[SubGameResult(outcome, 16, 20, 5)])


def test_build_arg_parser_defaults() -> None:
    args = main_module.build_arg_parser().parse_args([])
    assert args.config is None
    assert args.dry_run is False
    assert args.log_level == "INFO"
    assert args.output_dir == "results"


def test_main_dry_run_exits_zero_without_running_a_match(capsys, sample_config_data, tmp_path) -> None:
    config_path = tmp_path / "setup.json"
    config_path.write_text(json.dumps(sample_config_data), encoding="utf-8")

    exit_code = main_module.main(["--config", str(config_path), "--dry-run"])

    assert exit_code == 0
    assert "Config OK" in capsys.readouterr().out


def test_main_missing_config_file_exits_one(capsys, tmp_path) -> None:
    missing = tmp_path / "does_not_exist.json"
    exit_code = main_module.main(["--config", str(missing), "--dry-run"])
    assert exit_code == 1
    assert "Config error" in capsys.readouterr().err


def test_main_runs_a_full_match_and_writes_output(
    capsys, monkeypatch, sample_config_data, tmp_path
) -> None:
    config_path = tmp_path / "setup.json"
    config_path.write_text(json.dumps(sample_config_data), encoding="utf-8")
    output_dir = tmp_path / "out"

    class _FakeSDK:
        def __init__(self, config=None) -> None:
            self.config = config

        def run_match(self) -> GameResult:
            return _game_result(GameOutcome.COP_WIN)

        def send_match_report(self, result: GameResult) -> None:
            pass

    monkeypatch.setattr(main_module, "Hw6RaceSDK", _FakeSDK)

    exit_code = main_module.main(
        ["--config", str(config_path), "--output-dir", str(output_dir), "--log-level", "WARNING"]
    )

    assert exit_code == 0
    written = json.loads((output_dir / "last_match_result.json").read_text(encoding="utf-8"))
    assert written["totals"] == {"cop": 20, "thief": 5}
    assert "cop_total" not in capsys.readouterr().out  # summary uses the real schema, not ad-hoc keys


def test_build_arg_parser_bonus_flag_defaults_to_false() -> None:
    args = main_module.build_arg_parser().parse_args([])
    assert args.bonus is False


def test_main_bonus_flag_calls_run_bonus_match(
    monkeypatch, sample_config_data, tmp_path
) -> None:
    config_path = tmp_path / "setup.json"
    config_path.write_text(json.dumps(sample_config_data), encoding="utf-8")
    called: list = []

    class _FakeSDK:
        def __init__(self, config=None) -> None:
            pass

        def run_bonus_match(self) -> None:
            called.append(True)

    monkeypatch.setattr(main_module, "Hw6RaceSDK", _FakeSDK)

    exit_code = main_module.main(
        ["--config", str(config_path), "--bonus", "--log-level", "WARNING"]
    )

    assert exit_code == 0
    assert called == [True]


def test_main_returns_nonzero_when_a_sub_game_is_a_technical_loss(monkeypatch, sample_config_data, tmp_path) -> None:
    config_path = tmp_path / "setup.json"
    config_path.write_text(json.dumps(sample_config_data), encoding="utf-8")

    class _FakeSDK:
        def __init__(self, config=None) -> None:
            pass

        def run_match(self) -> GameResult:
            return _game_result(GameOutcome.TECHNICAL_LOSS)

        def send_match_report(self, result: GameResult) -> None:
            pass

    monkeypatch.setattr(main_module, "Hw6RaceSDK", _FakeSDK)

    exit_code = main_module.main(
        ["--config", str(config_path), "--output-dir", str(tmp_path / "out"), "--log-level", "WARNING"]
    )

    assert exit_code == 1

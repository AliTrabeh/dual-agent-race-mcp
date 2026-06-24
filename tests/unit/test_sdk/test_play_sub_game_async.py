from _orchestrator_doubles import FakeAgent, FakeMCPClient, RaisingAgent

from hw6_race.constants import GameOutcome, MoveDirection
from hw6_race.sdk.orchestrator import play_game_async, play_sub_game_async
from hw6_race.services.agents.models import ActionType, AgentAction
from hw6_race.shared.config import GameConfig


def _small_config() -> GameConfig:
    data = {
        "version": "1.00",
        "grid_size": [5, 5],
        "max_moves": 25,
        "num_games": 2,
        "max_barriers": 5,
        "scoring": {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5},
    }
    return GameConfig(data)


async def test_play_sub_game_async_breaks_immediately_on_a_thief_initiated_capture() -> None:
    """Thief moving onto the Cop's cell ends the sub-game before the Cop ever acts."""
    config = _small_config()
    thief_agent = FakeAgent(AgentAction(ActionType.MOVE, MoveDirection.UP))
    cop_agent = FakeAgent(AgentAction(ActionType.MOVE, MoveDirection.DOWN))
    thief_client, cop_client = FakeMCPClient(), FakeMCPClient()

    result = await play_sub_game_async(
        config, thief_agent, cop_agent, thief_client, cop_client, cop_start=(1, 2), thief_start=(2, 2)
    )

    assert result.outcome == GameOutcome.COP_WIN
    assert result.move_count == 1


async def test_play_game_async_records_a_technical_loss_without_crashing_the_match() -> None:
    config = _small_config()
    thief_agent = RaisingAgent(AgentAction(ActionType.MOVE, MoveDirection.UP))
    cop_agent = FakeAgent(AgentAction(ActionType.MOVE, MoveDirection.DOWN))
    thief_client, cop_client = FakeMCPClient(), FakeMCPClient()

    result = await play_game_async(config, thief_agent, cop_agent, thief_client, cop_client)

    assert len(result.sub_games) == config.num_games
    assert all(sg.outcome == GameOutcome.TECHNICAL_LOSS for sg in result.sub_games)
    assert all(sg.cop_points == 0 and sg.thief_points == 0 for sg in result.sub_games)

from hw6_race.constants import MoveDirection
from hw6_race.services.agents.models import ActionType, AgentAction, AgentObservation, Inference


def test_agent_action_move_carries_a_direction() -> None:
    action = AgentAction(action_type=ActionType.MOVE, direction=MoveDirection.UP)
    assert action.action_type == ActionType.MOVE
    assert action.direction == MoveDirection.UP


def test_agent_action_place_barrier_has_no_direction_by_default() -> None:
    action = AgentAction(action_type=ActionType.PLACE_BARRIER)
    assert action.direction is None


def test_agent_observation_defaults_to_an_empty_inbox() -> None:
    observation = AgentObservation(own_position=(0, 0), grid_size=(5, 5), barriers_remaining=5)
    assert observation.inbox == ()


def test_inference_carries_the_raw_text_unmodified() -> None:
    inference = Inference(believed_position=(1, 2), confidence="stated", raw_text="hi there")
    assert inference.raw_text == "hi there"

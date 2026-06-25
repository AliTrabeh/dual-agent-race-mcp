from hw6_race.constants import AgentRole, MoveDirection
from hw6_race.services.agents.models import ActionType, AgentObservation
from hw6_race.services.agents.strategies.llm_strategy import LLMDecisionStrategy


def _observation(
    position=(2, 2),
    grid_size=(5, 5),
    role=AgentRole.COP,
    barriers_remaining=0,
    believed_opponent_position=None,
) -> AgentObservation:
    return AgentObservation(
        own_position=position,
        grid_size=grid_size,
        barriers_remaining=barriers_remaining,
        role=role,
        believed_opponent_position=believed_opponent_position,
    )


def test_decide_returns_the_llm_chosen_legal_direction(fake_llm_client_factory) -> None:
    llm = fake_llm_client_factory(responses=["LEFT"])
    strategy = LLMDecisionStrategy(llm)

    action = strategy.decide(_observation())

    assert action.action_type == ActionType.MOVE
    assert action.direction == MoveDirection.LEFT


def test_decide_accepts_a_lowercase_response_with_extra_whitespace(fake_llm_client_factory) -> None:
    llm = fake_llm_client_factory(responses=["  down  "])
    strategy = LLMDecisionStrategy(llm)

    action = strategy.decide(_observation())

    assert action.direction == MoveDirection.DOWN


def test_decide_returns_place_barrier_for_cop_with_barriers_remaining(fake_llm_client_factory) -> None:
    llm = fake_llm_client_factory(responses=["PLACE_BARRIER"])
    strategy = LLMDecisionStrategy(llm)

    action = strategy.decide(_observation(role=AgentRole.COP, barriers_remaining=2))

    assert action.action_type == ActionType.PLACE_BARRIER
    assert action.direction is None


def test_decide_falls_back_when_thief_chooses_place_barrier(fake_llm_client_factory) -> None:
    llm = fake_llm_client_factory(responses=["PLACE_BARRIER"])
    strategy = LLMDecisionStrategy(llm)

    action = strategy.decide(_observation(position=(0, 0), role=AgentRole.THIEF))

    assert action.action_type == ActionType.MOVE  # fallback (HeuristicStrategy) never barriers


def test_decide_falls_back_when_cop_has_no_barriers_remaining(fake_llm_client_factory) -> None:
    llm = fake_llm_client_factory(responses=["PLACE_BARRIER"])
    strategy = LLMDecisionStrategy(llm)

    action = strategy.decide(_observation(position=(0, 0), role=AgentRole.COP, barriers_remaining=0))

    assert action.action_type == ActionType.MOVE


def test_decide_falls_back_when_llm_chooses_an_illegal_direction(fake_llm_client_factory) -> None:
    """At (0, 0), UP is out of bounds."""
    llm = fake_llm_client_factory(responses=["UP"])
    strategy = LLMDecisionStrategy(llm)

    action = strategy.decide(_observation(position=(0, 0)))

    assert action.direction == MoveDirection.RIGHT  # fallback default for the top-left corner


def test_decide_falls_back_when_response_is_unparseable(fake_llm_client_factory) -> None:
    llm = fake_llm_client_factory(responses=["I'm not sure what to do"])
    strategy = LLMDecisionStrategy(llm)

    action = strategy.decide(_observation(position=(0, 0)))

    assert action.direction == MoveDirection.RIGHT


def test_decide_falls_back_when_response_is_empty(fake_llm_client_factory) -> None:
    llm = fake_llm_client_factory(responses=[""])
    strategy = LLMDecisionStrategy(llm)

    action = strategy.decide(_observation(position=(0, 0)))

    assert action.direction == MoveDirection.RIGHT


def test_decide_falls_back_when_llm_raises(fake_llm_client_factory) -> None:
    llm = fake_llm_client_factory(raises=RuntimeError("backend down"))
    strategy = LLMDecisionStrategy(llm)

    action = strategy.decide(_observation(position=(0, 0)))

    assert action.direction == MoveDirection.RIGHT


def test_prompt_mentions_the_belief_when_present(fake_llm_client_factory) -> None:
    llm = fake_llm_client_factory(responses=["LEFT"])
    strategy = LLMDecisionStrategy(llm)

    strategy.decide(_observation(believed_opponent_position=(3, 3)))

    assert "(3, 3)" in llm.prompts_seen[0]


def test_prompt_omits_barrier_option_for_thief(fake_llm_client_factory) -> None:
    llm = fake_llm_client_factory(responses=["LEFT"])
    strategy = LLMDecisionStrategy(llm)

    strategy.decide(_observation(role=AgentRole.THIEF))

    assert "PLACE_BARRIER" not in llm.prompts_seen[0]


def test_prompt_includes_barrier_option_for_cop_with_barriers_remaining(
    fake_llm_client_factory,
) -> None:
    llm = fake_llm_client_factory(responses=["LEFT"])
    strategy = LLMDecisionStrategy(llm)

    strategy.decide(_observation(role=AgentRole.COP, barriers_remaining=3))

    assert "PLACE_BARRIER" in llm.prompts_seen[0]

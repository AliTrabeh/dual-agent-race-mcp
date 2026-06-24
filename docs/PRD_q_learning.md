# PRD — Q-Learning Decision Strategy (per-mechanism PRD)

> Required by Guidelines PDF SG-D03 for any significant algorithm. This covers the **optional** Tabular Q-Learning decision strategy named in the HW PDF (HW-F20, p.8-10). Source reference implementation is reproduced/adapted from the HW PDF's own example code.

## Background / Context

The HW PDF recommends — but does not require — Tabular Q-Learning as the decision-making mechanism for one or both agents (it explicitly says heuristics, minimum-distance reasoning, or prompt engineering alone are equally acceptable; grading is about MCP orchestration, not algorithm sophistication — HW-F03). This PRD exists so that *if* Q-Learning is implemented, it follows a single, reviewed design rather than being improvised mid-chunk, per the "no vibe coding" rule (SG-P01).

## Input / Output Specification

- **Input (state)**: current agent position encoded as a flat grid index `0..grid_size[0]*grid_size[1]-1` (matches the HW PDF's `num_states = 25` example for a 5×5 board).
- **Input (training signal)**: reward `r` per the scoring table in `config/setup.json` (`scoring.cop_win`, `scoring.thief_win`, `scoring.cop_loss`, `scoring.thief_loss`), plus a small per-step penalty for "kalad" mechanics — to be finalized per ADR if used (this PRD intentionally does **not** invent a step-penalty value not present in the source PDF; if not specified by the user, none is added beyond the explicit win/loss rewards).
- **Output**: an action index in `0..3` (4 movement directions) chosen via epsilon-greedy over the Q-table; barrier-placement (Cop-only, 5th action) is out of scope for the v1 Q-table unless explicitly requested, since the source PDF's example code only models `num_actions = 4`.
- **Setup data**: `learning_rate` (α, default 0.1), `discount_factor` (γ, default 0.9), epsilon schedule for the epsilon-greedy policy — all sourced from config, never hard-coded (SG-C08).

## Components / Files Likely Needed

- `services/agents/strategies/q_learning_strategy.py` — implements the shared `DecisionStrategy` interface (ADR-003 in `docs/PLAN.md`); ≤150 lines, delegating the Bellman update to a small pure function for testability.
- `services/agents/strategies/heuristic_strategy.py` — the default, non-RL counterpart, same interface.
- `config/setup.json` — adds a `q_learning` config block (`learning_rate`, `discount_factor`, `epsilon`) if this strategy is enabled.

## Acceptance Criteria

- Q-table update exactly matches the Bellman equation given in the HW PDF: `Q(s,a) ← Q(s,a) + α[r + γ·max_a' Q(s',a') − Q(s,a)]`.
- Strategy is selected via config (`decision_strategy: "heuristic" | "q_learning"`), not a code branch requiring a rebuild.
- Swapping strategies does not require any change to `services/mcp` or `services/race` — proves the Strategy pattern boundary (ADR-003) actually holds.
- If used, the README includes a learning-curve plot (per HW-F26) showing convergence across the staged sanity-check grid sizes (2×2 → 5×5).

## Edge Cases

- `done` terminal state (capture or move-limit reached) must use `best_next_q = 0.0`, matching the HW PDF's reference code exactly — a common Q-learning bug is forgetting to zero out the terminal bootstrap.
- Q-table dimensions must follow `grid_size` from config dynamically (`num_states = grid_size[0] * grid_size[1]`), not a hard-coded `25`, since HW-F06 requires grid size to be configurable.
- Epsilon-greedy must not become fully greedy (epsilon=0) before a minimum number of training episodes, to avoid premature convergence on a degenerate policy during the small sanity-check grids.

## Testing Requirements

- Unit test the Bellman update function directly against hand-computed expected values (pure function, no I/O — easy to hit 100% coverage here specifically).
- Unit test terminal-state handling (`done=True` ⇒ no bootstrap from next state).
- Integration test: running the strategy across the 2×2 sanity-check grid for N episodes shows non-decreasing average reward (a basic convergence smoke test, not a statistical proof).

## Risks

- Tabular Q-Learning does not scale state-space-wise if `grid_size` grows large or if Cop's barrier placements are added to the state encoding — explicitly out of scope for v1, flagged here rather than silently ignored.
- Optional feature creep risk: because the HW PDF explicitly deprioritizes algorithm sophistication versus orchestration quality (HW-F03), this strategy must not consume implementation time needed for the MCP/communication layer, which is what's actually graded.

## Definition of Done

- `DecisionStrategy` interface exists and the heuristic implementation satisfies it, with or without Q-Learning being implemented at all.
- If Q-Learning is implemented: passes its dedicated unit tests, is config-toggleable, and is documented in the README's learning-curve section.
- If Q-Learning is *not* implemented for v1: this PRD remains as a ready-to-execute spec for a future chunk, and `docs/01_requirements_matrix.md` HW-F20 status reflects "stretch / not started" rather than being silently dropped.

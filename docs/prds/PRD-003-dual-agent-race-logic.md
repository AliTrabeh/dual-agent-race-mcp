# PRD-003 — Dual Agent Race Logic

## Purpose

Implement the actual pursuit-game rules — grid, movement, barriers, capture/survival win conditions, and scoring — independent of how the agents decide to move or how they talk to each other. This is the deterministic core that everything else (MCP layer, agent decision strategies, orchestrator, reporting) wraps around. Because the HW PDF explicitly states grading is about MCP orchestration quality rather than algorithmic cleverness (HW-F03), this chunk must be correct and simple rather than clever.

## Scope

In scope: `services/race/race_state.py` (grid representation, agent positions, barrier set, legality checks), `services/race/race_engine.py` (turn loop: Thief moves first then Cop, alternating, move counter, win-condition checks), `services/race/scoring.py` (scoring table lookups against config). One sub-game (≤25 moves) and the aggregation of 6 sub-games into a full game are both in scope.

Out of scope: natural-language interpretation of agent intent (chunk 4/agents), MCP transport (chunk 2/already built), the orchestrator loop tying sub-games to actual agent calls (chunk 6), and reporting/email (chunk 7) — this chunk exposes a pure, synchronous API that chunk 6 calls.

## Requirements Covered

HW-F04 (sub-game ≤25 moves, alternating turns, Thief first), HW-F05 (game = 6 sub-games, aggregated), HW-F06 (configurable grid size), HW-F07 (start positions, 4-direction movement, full grid state per move), HW-F08 (Cop capture win), HW-F09 (Thief survival win), HW-F10 (barriers: max 5, Cop-only, one-way blocking only against Cop), HW-F11 (scoring table: 20/5 cop-win, 10/5 thief-win), HW-F25 (no hard-coded parameters — everything sourced from `config/setup.json`). SG-C13 (building-block design: each class documents Input/Output/Setup explicitly).

## Inputs and Outputs

**Inputs**: `config/setup.json` values (`grid_size`, `max_moves`, `num_games`, `max_barriers`, `scoring.*`); a sequence of legal actions chosen by each agent's decision strategy (movement direction, or barrier-placement for the Cop).

**Outputs**: updated `RaceState` per action; a terminal result per sub-game (`cop_win` / `thief_win` / `technical_loss`), with the associated scoring applied; an aggregated `GameResult` across all 6 sub-games, ready for `services/reporting` to serialize.

## Components / Files Likely Needed

- `services/race/race_state.py` — `RaceState` class: grid dims, cop/thief positions, barrier positions (set, max 5), move count; `apply_action()`, `is_legal(action)`, `check_win_condition()`.
- `services/race/race_engine.py` — `RaceEngine` class: runs one sub-game given two action-providers (callables), and a `play_game()` method running 6 sub-games back to back, building a `GameResult`.
- `services/race/scoring.py` — pure functions mapping a sub-game outcome to `(cop_points, thief_points)` from config, no hard-coded numbers.
- `services/race/models.py` — small dataclasses (`SubGameResult`, `GameResult`) if needed to stay under 150 lines per file (split per SG-C01 guidance: "split model definitions into their own file").

## Acceptance Criteria

- A sub-game terminates in capture (Cop on Thief's cell) → recorded as `cop_win`, scoring exactly 20/5 by default config.
- A sub-game reaches move 25 with no capture → recorded as `thief_win`, scoring exactly 10/5 by default config.
- Cop placing a 6th barrier in one sub-game is rejected as illegal, not silently capped.
- Thief attempting to place a barrier at all is rejected — barriers are Cop-only.
- A barrier blocks only the Cop's movement through that cell on subsequent moves; the Thief can move through the same cell freely.
- **Corrected bound (see HW-Q08 in `docs/07_risks_and_open_questions.md`)**: for a *fixed-role* local match (one agent always Cop, the other always Thief across all 6 sub-games — the normal case for Chunks 5/6's local testing), the provable bounds are `cop_total ∈ [30, 120]` and `thief_total ∈ [30, 60]` (derived: `cop_total = 15·w + 30`, `thief_total = 60 − 5·w`, where `w` = number of Cop wins, `w ∈ [0,6]`). The HW PDF's literal "max 90 / min 30" figure (`3×20 cop + 3×10 thief`) only arises when a single group's score is aggregated across a 3-Cop-role + 3-Thief-role split, which the HW PDF only explicitly describes for the inter-group bonus round (HW-F27). Tests assert the corrected bound, not the literal PDF figure, for fixed-role local matches.
- Grid size, move cap, barrier cap, and all scoring values come from config; changing `config/setup.json` changes engine behavior with no code change.

## Edge Cases

- Non-square grid (e.g., `grid_size: [4, 6]`) — engine must not assume square dimensions anywhere.
- Cop and Thief starting on the same cell (if randomization allows it) — must be treated as an immediate capture/cop-win, not an undefined state, unless config explicitly disallows same-cell starts (decide and document explicitly, don't leave ambiguous).
- Move 25 exactly — off-by-one risk: confirm whether "25 moves" means 25 total moves combined or 25 moves *each*; per the source PDF wording ("the Thief survives 25 moves without the Cop landing on its cell along the length of the sub-game"), this is interpreted as 25 *total* moves in the sub-game; flagged for explicit unit test coverage of the boundary.
- Barrier placed on the Cop's own current cell vs. an arbitrary cell — source PDF says "the Cop may place a barrier on the cell it currently occupies," so placement targets are restricted to the Cop's current position only, not arbitrary board cells; this must be enforced, not left permissive.

## Testing Requirements

Exhaustive unit tests on `RaceState` (legality, win conditions, barrier limits, boundary move counts) and `scoring.py` (table lookups against varied config values, not just defaults). Table-driven tests assert exact expected point totals for known win/loss sequences (not the literal "30–90" PDF figure — see the corrected bound above) across many scripted sub-game outcome sequences. No mocking needed here since this layer has no external dependencies — purely deterministic, which makes it the easiest chunk to hit 100% coverage on, helping offset chunks with unavoidable mocking overhead elsewhere.

## Risks

Ambiguity in "25 moves" (total vs. per-agent) and "starting positions" (random vs. strategic) are both flagged as `[Needs confirmation]` in `docs/07_risks_and_open_questions.md` (HW-Q07) — this PRD documents the interpretation chosen so it's auditable, not buried in code.

## Definition of Done

`RaceEngine.play_game()` runs a full 6-sub-game match against two scripted/stub action providers in a test, produces a `GameResult` with correct totals, all files ≤150 lines, ≥85% coverage on this module specifically, and `docs/TODO.md`'s "Chunk 5" row updated to `done`.

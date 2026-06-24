# 05 — Testing Strategy

## 1. Governing rules

- TDD, Red-Green-Refactor, tests written before/alongside implementation (SG-T01).
- Every module → matching test file; every public function → ≥1 test, covering both happy path and at least one error/edge path (SG-T02).
- Layout: `tests/unit/test_<module>/test_<file>.py` mirrors `src/`; `tests/integration/test_<feature>.py`; shared fixtures in `tests/conftest.py` (SG-T03).
- All external dependencies (LLM API, Gmail API, MCP network calls) are mocked in unit tests; **no test may depend on a live external service** (SG-T03).
- Global coverage ≥85%, enforced via `pyproject.toml` (`fail_under = 85`), excluding `src/main.py`, `*/tests/*`, any future `src/**/gui/*` (SG-T04).
- Ruff must report 0 warnings (SG-T07) — treated as part of the test gate, run alongside `pytest`.
- `tests/test_line_limits.py` enforces the project's 150-physical-line cap (PROJ-R01, stricter than SG-C01) on every `.py` file under `src/`, `tests/`, `tools/` and is treated as part of the standard test run, not an optional extra.

## 2. Mapping the HW PDF's staged sanity checks onto the test suite

The HW PDF's 4-stage sanity-check table (HW-F12) is implemented as parametrized integration tests, not as separate code paths — see `tests/integration/test_staged_sanity_checks.py` (Chunk 9), parametrized over `[(2,2), (3,3), (3,2), (4,4), (4,3), (5,5)]`:

| Stage | Grid | What the test asserts |
|-------|------|--------------------------|
| 1 | 2×2 | A minimal sub-game completes in finite moves; MCP message pipeline transmits and is received without transformation loss |
| 2 | 3×3 / 3×2 | Coordination mechanisms engage (e.g., hyperparameters are read from config, not hard-coded); no silent failure modes |
| 3 | 4×4 / 4×3 | Partial observability matters — i.e., Cop cannot win in 1 move purely from full board knowledge; capture/escape both reachable depending on seed |
| 4 | 5×5 | Full final run: 6 sub-games, JSON report generated, scoring totals fall within [30, 90] |

These live in `tests/integration/test_staged_sanity_checks.py`, parametrized over `grid_size`.

## 3. Test types and what they cover

- **Unit — `services/race`**: legal-move validation, barrier placement limits (max 5, Cop-only), capture detection, survival win condition, scoring table lookups against `config/setup.json`, all boundary cases (move 0, move 25, move 26 rejected, barrier 5 vs 6).
- **Unit — `services/mcp`**: token auth accept/reject/revoke, tool registration, message pass-through with no transformation (asserts the server does not "peek" at opponent state).
- **Unit — `services/agents`**: `DecisionStrategy` interface contract tests (heuristic and, later, Q-Learning implementations each get their own test module per SG-C04's "independently testable" mixin rule); malformed/ambiguous NL message handling (graceful degradation, SG-T05).
- **Unit — `shared/gatekeeper.py`**: rate-limit enforcement before call, queuing on limit breach, retry-after behavior, queue-depth/backpressure, all using a fake clock — no real sleeping in tests.
- **Unit — `services/reporting`**: schema validation for both JSON report types against the exact examples in `docs/00_source_analysis.md` HW-F23/F24; Technical Loss flagging logic.
- **Integration — `tests/integration`**: full local 6-sub-game run with both MCP servers started in-process (or via test doubles), end-to-end through the SDK entry point; staged sanity-check matrix (above).

## 4. Edge cases register (SG-T05)

| Edge case | Expected behavior | Test reference |
|-----------|----------------------|------------------|
| Cop attempts a 6th barrier in one sub-game | Rejected, no state mutation, clear error | `test_race_state.py::test_barrier_limit_enforced` |
| Sub-game reaches move 25 with no capture | Thief win recorded, sub-game closes cleanly | `test_race_state.py::test_thief_survives_to_move_limit` |
| MCP call fails mid-sub-game (network/timeout) | Sub-game marked Technical Loss, rerun triggered, not silently dropped | `test_reporting.py::test_technical_loss_flagging` |
| Agent LLM returns unparseable/ambiguous text | Receiving agent falls back to a default safe action, logs the ambiguity, does not crash | `test_base_agent.py::test_malformed_message_degrades_gracefully` |
| Rate limit exceeded on LLM or Gmail API call | Call is queued, not dropped or retried unboundedly; backpressure alert raised at max depth | `test_gatekeeper.py::test_queue_backpressure` |
| Grid size changed via config to non-square (e.g., 4×6) | Engine still functions; no assumption of square grid baked into code | `test_race_state.py::test_non_square_grid` |

## 5. Reporting test results (SG-T06)

`uv run pytest --cov=src --cov-report=term-missing tests/` is the canonical local command (once `uv` is installed — see `docs/07_risks_and_open_questions.md`). Output (pass/fail counts, coverage %) is captured in `docs/08_claude_work_log.md` after each significant chunk, alongside the prompt that produced the change.

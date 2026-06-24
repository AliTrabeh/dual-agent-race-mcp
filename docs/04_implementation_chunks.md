# 04 — Implementation Chunk Plan

Chunks 0–11, ordered to satisfy both the Guidelines PDF's SDLC stage order (SG-P02: requirements → architecture → TDD → validation → deployment → maintenance) and the HW PDF's own recommended 8-stage development priority (HW-F29: grid rules → MCP infra → local run → decision strategy → NL protocol → optional GUI → cloud deploy → Gmail integration). Each chunk lists Goal, Files, Requirements covered, Dependencies, Steps, Tests, Expected output, Done criteria. No chunk after 1 should start until the previous chunk's Done criteria are met and `docs/TODO.md` is updated.

> **Project rule (PROJ-R01, see `docs/00_source_analysis.md` §9a)**: every `.py` file produced in **every** chunk below must stay ≤150 physical lines (blank lines and comments counted), enforced automatically by `tests/test_line_limits.py`. This is stricter than SG-C01's 150-*logical*-line cap. Any chunk whose planned file list risks exceeding this — most notably Chunk 5 (race engine) and Chunk 6 (orchestrator) — must split work across additional small files (e.g. `race_state.py` / `race_engine.py` / `scoring.py` / `models.py` are already split for this reason) rather than requesting an exception. "Done criteria" for every chunk implicitly includes "`tests/test_line_limits.py` passes for all files this chunk adds or touches," even where not repeated verbatim below.

---

## Chunk 0 — Project initialization and repository structure

- **Goal**: Establish the directory skeleton, `pyproject.toml`, `.gitignore`, `.env-example` — nothing executable yet beyond import-safe stubs.
- **Files**: `pyproject.toml`, `.gitignore`, `.env-example`, `src/hw6_race/__init__.py`, all subpackage `__init__.py` files, `outputs/.gitkeep`.
- **Requirements covered**: SG-D04 (canonical layout), SG-U01/U02 (uv + pyproject.toml, no requirements.txt), SG-C11 (package hygiene).
- **Dependencies**: none (first chunk).
- **Steps**: 1) create directory tree per `docs/01_requirements_matrix.md`; 2) write `pyproject.toml` with project metadata + `[tool.ruff]`/`[tool.coverage]` sections; 3) write `.gitignore` (`.env`, `*.key`, `*.pem`, `credentials.json`, `__pycache__/`, `.venv/`); 4) write `.env-example` with placeholder keys.
- **Tests**: `python -c "import hw6_race"` succeeds (manual check; once `uv` is installed, `uv run python -c "import hw6_race"`).
- **Expected output**: a clean, importable, empty package.
- **Done criteria**: directory tree matches the matrix exactly; `tests/test_line_limits.py` passes (no `.py` file >150 physical lines); `docs/TODO.md` Chunk 0 row → done.

## Chunk 1 — Requirements extraction and validation checklist

- **Goal**: (This chunk is already complete as of this session.) Produce `docs/00_source_analysis.md`, `docs/01_requirements_matrix.md`, all PRDs, and this chunk plan.
- **Files**: all of `docs/`.
- **Requirements covered**: SG-P01/P02/D02/D03/D05.
- **Dependencies**: none.
- **Steps**: read both PDFs fully; extract requirements; build matrix; write PRDs; write chunk plan.
- **Tests**: n/a (documentation chunk) — validated by human review/approval.
- **Expected output**: the full `docs/` tree as committed in this session.
- **Done criteria**: user has reviewed and approved the documents before chunk 2 begins (per SG-D05's "approve before coding" rule) — **this is a hard gate the assistant must not skip past.**

## Chunk 2 — Core config system

- **Goal**: `shared/config.py`, `shared/version.py`, `shared/gatekeeper.py`, `constants.py`, `config/setup.json`, `config/rate_limits.json`.
- **Files**: see PRD-001.
- **Requirements covered**: HW-F06/F25, SG-C05–C10.
- **Dependencies**: Chunk 0.
- **Steps**: 1) define `constants.py` enums/defaults; 2) implement `ConfigLoader` reading + validating `config/setup.json` against required keys (HW-F25); 3) implement `ApiGatekeeper` per the literal interface in the Guidelines PDF; 4) implement `version.py` returning `"1.00"`; 5) write unit tests for all of the above (TDD: tests alongside implementation).
- **Tests**: `tests/unit/test_shared/{test_config.py,test_version.py,test_gatekeeper.py}`.
- **Expected output**: config loads, validates, and the Gatekeeper enforces rate limits against a fake clock in tests.
- **Done criteria**: PRD-001 acceptance criteria met; `tests/test_line_limits.py` passes for all files this chunk adds; `docs/TODO.md` Chunk 2 → done.

## Chunk 3 — MCP server/server layer

- **Goal**: Two independent FastMCP servers (Cop, Thief) with token auth + revoke.
- **Files**: see PRD-002.
- **Requirements covered**: HW-F13/F14/F15/F17/F18.
- **Dependencies**: Chunk 2 (config, Gatekeeper for any outbound calls the servers make).
- **Steps**: 1) `server_base.py` auth + tool registration scaffold; 2) `auth.py` token issue/verify/revoke; 3) `server_a.py`/`server_b.py` agent-specific tools; 4) `client.py` minimal MCP client wrapper.
- **Tests**: unit tests for auth (valid/invalid/expired/revoked tokens); integration test starting both servers on ephemeral ports and round-tripping a message.
- **Expected output**: `uv run python -m hw6_race.services.mcp.server_a` (and `_b`) start standalone; a test client can call their tools successfully with a valid token, and is rejected without one.
- **Done criteria**: PRD-002 acceptance criteria met; `tests/test_line_limits.py` passes for all files this chunk adds; `docs/TODO.md` Chunk 3 → done.

## Chunk 4 — Agent abstraction layer

- **Goal**: `base_agent.py`, `cop_agent.py`, `thief_agent.py`, `llm_client.py`, plus the `DecisionStrategy` interface and a default heuristic implementation.
- **Files**: see PRD-004 (agent half) and PRD-003 (`DecisionStrategy` interface lives conceptually with the race domain but is consumed by agents).
- **Requirements covered**: HW-F02/F15/F19, SG-C04.
- **Dependencies**: Chunk 2 (Gatekeeper), Chunk 3 (MCP client for agents to call through).
- **Steps**: 1) define `LLMClient` interface + one concrete cloud-API implementation, routed through the Gatekeeper; 2) define `DecisionStrategy` interface + `HeuristicStrategy`; 3) `base_agent.py` composing both, with `decide_action`/`compose_message`/`interpret_message`; 4) `cop_agent.py`/`thief_agent.py` thin subclasses.
- **Tests**: unit tests for message interpretation (well-formed/malformed/ambiguous), strategy decision logic, all with mocked `LLMClient`.
- **Expected output**: a Cop agent and Thief agent object, each able to produce a message and a legal action given a mocked LLM response.
- **Done criteria**: PRD-004's agent-side acceptance criteria met; `tests/test_line_limits.py` passes for all files this chunk adds; `docs/TODO.md` Chunk 4 → done.

## Chunk 5 — Dual-agent race mechanism

- **Goal**: `race_state.py`, `race_engine.py`, `scoring.py`, `models.py` — the deterministic game core.
- **Files**: see PRD-003.
- **Requirements covered**: HW-F04/F05/F06/F07/F08/F09/F10/F11/F25.
- **Dependencies**: Chunk 2 (config for parameters).
- **Steps**: 1) `RaceState` with grid/positions/barriers/move-count and legality checks; 2) win-condition checks (capture, survival); 3) `scoring.py` table lookups from config; 4) `RaceEngine.play_sub_game()` and `.play_game()` (6 sub-games); 5) exhaustive unit tests including boundary cases (move 25, barrier 5/6, non-square grid).
- **Tests**: see PRD-003 Testing Requirements — this is the easiest module to push toward 100% coverage given no external dependencies.
- **Expected output**: `RaceEngine.play_game()` runs to completion against two scripted/stub action providers, producing a `GameResult` whose totals match the corrected bound for a fixed-role local match — `cop_total ∈ [30, 120]`, `thief_total ∈ [30, 60]` (see HW-Q08 in `docs/07_risks_and_open_questions.md`; the literal HW PDF "90/30" figure applies only to the bonus round's 3-Cop-role + 3-Thief-role aggregate, not a fixed-role local match).
- **Done criteria**: PRD-003 acceptance criteria met; `tests/test_line_limits.py` passes for all files this chunk adds — split `race_state.py`/`race_engine.py`/`scoring.py`/`models.py` further if any approaches 120 lines; `docs/TODO.md` Chunk 5 → done. *(Optional stretch within this chunk's timeframe: `docs/PRD_q_learning.md`'s `QLearningStrategy`, behind the same `DecisionStrategy` interface from Chunk 4 — only if time/scope allows; HW-F20 is explicitly optional.)*

## Chunk 6 — Controller / orchestrator / game loop

- **Goal**: `sdk/sdk.py`'s `Hw6RaceSDK.run_local_match()` tying Chunks 3–5 together into one runnable match.
- **Files**: see PRD-004 (orchestrator half).
- **Requirements covered**: HW-F01/F02/F15, SG-C03.
- **Dependencies**: Chunks 2, 3, 4, 5 all complete.
- **Steps**: 1) `sdk.py` constructs both agents, both MCP servers/clients, and the `RaceEngine`; 2) per-turn loop: agent composes message → MCP tool call → opponent receives → opponent infers/derives action → engine applies action → repeat until sub-game terminal; 3) Technical Loss detection wiring (calls into Chunk 7's stub, finalized there); 4) full per-turn trace logging.
- **Tests**: integration test running a full mocked-LLM, real-engine, real-or-in-process-MCP match end to end.
- **Expected output**: one SDK call produces a complete `GameResult` plus a readable trace log.
- **Done criteria**: PRD-004 full acceptance criteria met (both agent-side and orchestrator-side); `tests/test_line_limits.py` passes — split `sdk.py`'s turn-loop into a helper module if it risks exceeding 150 physical lines; `docs/TODO.md` Chunk 6 → done.

## Chunk 7 — Logging, JSON protocol, and run history

- **Goal**: `services/reporting/{schemas.py, run_logger.py, technical_loss.py, mailer.py}`.
- **Files**: see PRD-005.
- **Requirements covered**: HW-F21/F22/F23/F24/F28.
- **Dependencies**: Chunk 6 (needs a real `GameResult` to report on).
- **Steps**: 1) `schemas.py` typed structures matching the HW PDF's literal JSON examples; 2) `run_logger.py` accumulating sub-game results as Chunk 6's loop progresses; 3) `technical_loss.py` rerun bookkeeping; 4) `mailer.py` Gmail OAuth dispatch through the Gatekeeper, JSON-only body.
- **Tests**: schema validation against literal PDF examples; Technical Loss/rerun bookkeeping; fully mocked mailer tests.
- **Expected output**: after a completed match, a validated Internal Game JSON is produced and (with real credentials) emailed.
- **Done criteria**: PRD-005 acceptance criteria met; `tests/test_line_limits.py` passes for all files this chunk adds; `docs/TODO.md` Chunk 7 → done.

## Chunk 8 — CLI interface

- **Goal**: A thin `main.py` exposing a runnable command, calling only `sdk/sdk.py` — zero business logic in the CLI itself (SG-C03).
- **Files**: `src/hw6_race/main.py`.
- **Requirements covered**: SG-C03 (SDK-only CLI), implicit HW requirement for "CLI run evidence" (HW-F26).
- **Dependencies**: Chunks 2–7.
- **Steps**: 1) argument parsing (config path override, dry-run flag); 2) call `Hw6RaceSDK.run_local_match()`; 3) pretty-print a human-readable summary of the trace + final JSON.
- **Tests**: a smoke test invoking `main()` with mocked SDK to confirm wiring, plus the real end-to-end test already covered in Chunk 6/9.
- **Expected output**: `uv run python -m hw6_race.main` runs a full local match and prints results.
- **Done criteria**: CLI contains no business logic (verified by code review against SG-C03); `tests/test_line_limits.py` passes; `docs/TODO.md` Chunk 8 → done.

## Chunk 9 — Tests (suite-level completion)

- **Goal**: Close any coverage/lint gaps left by per-chunk TDD; run the staged sanity-check matrix; produce the suite-level report.
- **Files**: see PRD-006.
- **Requirements covered**: SG-T01–T07, HW-F12.
- **Dependencies**: Chunks 0–8.
- **Steps**: see PRD-006 Steps/Components.
- **Tests**: the suite itself, plus `tests/integration/test_staged_sanity_checks.py`.
- **Expected output**: `pytest --cov` ≥85%, `ruff check` 0 warnings, all 4 sanity-check stages pass.
- **Done criteria**: PRD-006 acceptance criteria met, including `tests/test_line_limits.py` passing project-wide as part of the suite-level gate; `docs/TODO.md` Chunk 9 → done.

## Chunk 10 — Documentation and submission packaging

- **Goal**: Finalize README, deploy MCP servers to the cloud, prepare bonus-round documentation.
- **Files**: see PRD-007.
- **Requirements covered**: HW-F16/F26/F27/F28, SG-D01, SG-U03.
- **Dependencies**: Chunks 0–9.
- **Steps**: see PRD-007 Steps/Components.
- **Tests**: fresh-clone smoke test.
- **Expected output**: a public, deployed, documented submission.
- **Done criteria**: PRD-007 acceptance criteria met; `tests/test_line_limits.py` still passes after the fresh-clone smoke test; `docs/TODO.md` Chunk 10 → done.

## Chunk 11 — Final validation against both PDFs

- **Goal**: Walk `docs/06_submission_checklist.md` end-to-end against the actual repository state; close any gaps found.
- **Files**: n/a (validation pass, may produce small fixes anywhere).
- **Requirements covered**: all of them, as a final audit.
- **Dependencies**: Chunks 0–10.
- **Steps**: 1) re-read both PDFs once more; 2) tick every checklist box or document why it's N/A; 3) re-run the full test+lint gate; 4) update `docs/01_requirements_matrix.md` status column to ✅ across the board (or document remaining gaps honestly).
- **Tests**: full suite re-run.
- **Expected output**: a submission-ready repository with no known undocumented gap.
- **Done criteria**: `docs/06_submission_checklist.md` fully checked or justified, including the Python file line-limit check and PRD-count check; `docs/TODO.md` Chunk 11 → done.

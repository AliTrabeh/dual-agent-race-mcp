# 08 — Claude Work Log / Prompt Engineering Log

Doubles as the Prompt Engineering Log mandated by Guidelines PDF SG-U04 (prompt text/context, output, iterations, lessons learned) and as a running decision log for this project's AI-assisted development.

---

## Entry 1 — 2026-06-24 — Phase 0/1 planning session

**Prompt context/goal**: User asked for a full requirement-analyst pass over both governing PDFs (`ex06-Dual AI agent race via MCP servers.pdf`, `software_submission_guidelines-V3.pdf`) before any implementation, followed by a documentation structure (Phase 1), chunk plan (Phase 2), minimal skeleton (Phase 3), and README (Phase 4) — explicitly forbidding full implementation in this pass.

**What was done**:
1. Verified working directory `C:\Users\atrab\OneDrive\Desktop\AI Agents\HW6` and confirmed both required PDFs are present.
2. Read both PDFs in full (HW PDF: 17 pages, single pass; Guidelines PDF: 39 pages, in two 20/19-page chunks due to tool page limits).
3. Extracted all functional/non-functional/process requirements into `docs/00_source_analysis.md`, explicitly marking unresolved items as `[Needs confirmation]` rather than guessing.
4. Built `docs/01_requirements_matrix.md` tracing every requirement ID to a planned artifact, chunk, and status.
5. Wrote the guideline-mandated `docs/PRD.md`, `docs/PLAN.md`, `docs/TODO.md` (exact filenames required by the Guidelines PDF), plus the narrative `docs/02_master_prd.md`, `docs/03_architecture.md`, `docs/05_testing_strategy.md`, `docs/06_submission_checklist.md`, `docs/07_risks_and_open_questions.md`, and this log.

**Key decisions / lessons learned**:
- The two PDFs conflict on dependency tooling: the user's own suggested skeleton (in the original task prompt) included `requirements.txt`, but the Guidelines PDF explicitly forbids it in favor of `uv` + `pyproject.toml`. Resolved in favor of the Guidelines PDF (documented in `00_source_analysis.md` §9) since it is the authoritative submission-standard document.
- Discovered `uv` is not installed/on PATH in this environment even though PyCharm's `.idea` config references a "uv (HW6)" interpreter — flagged as a blocking technical risk in `07_risks_and_open_questions.md`, not silently worked around.
- Kept architecture documentation (`PLAN.md`) deliberately shallow at the class-diagram level (ADR-002) to avoid speculative design for code that doesn't exist yet, while still satisfying the "architecture before code" rule at the container/component level.
- Treated the HW PDF's Q-Learning recommendation as explicitly optional per its own wording ("p.8: Reinforcement learning ... is optional and recommended only") — default plan ships a heuristic strategy first behind a shared interface.

**Next planned entry**: after chunk-level PRDs (`docs/prds/`) and the chunk plan (`docs/04_implementation_chunks.md`) are written, and again after the skeleton/README land.

---

## Entry 2 — 2026-06-24 — Phase 2/3/4/5: chunk plan, skeleton, README

**Prompt context/goal**: Continuation of the same session — write the chunk-by-chunk implementation plan, create the project skeleton following the canonical layout from `docs/01_requirements_matrix.md`, write the root README, and add minimal import-safe code with basic tests, per the user's explicit instruction not to implement full game logic yet.

**What was done**:
1. Wrote `docs/04_implementation_chunks.md` (chunks 0–11) and the 7 chunk-level PRDs in `docs/prds/`, plus `docs/PRD_q_learning.md`.
2. Created the full directory skeleton (`src/hw6_race/{sdk,shared,services/{agents,mcp,race,reporting}}`, `tests/`, `config/`, `data/`, `results/`, `assets/`, `outputs/`).
3. Wrote `pyproject.toml` (uv/pyproject-based, no `requirements.txt`, with `[tool.ruff]` and `[tool.coverage]` sections matching the Guidelines PDF exactly), `.gitignore`, `.env-example`, `config/setup.json`, `config/rate_limits.json`.
4. Implemented (not just stubbed) the Chunk 2 infrastructure ahead of schedule, since it's small and foundational: `constants.py`, `shared/version.py`, `shared/config.py` (config loader/validator with typed errors), `shared/gatekeeper.py` (full `ApiGatekeeper` with FIFO-style rate limiting, backpressure, injectable clock for deterministic tests). `sdk/sdk.py` and `services/*` remain deliberate stubs (`NotImplementedError` pointing at the responsible chunk/PRD) since their real logic depends on chunks not yet started.
5. Wrote `tests/conftest.py` (fixtures incl. a `FakeClock`), `tests/test_basic_imports.py`, and `tests/unit/test_shared/{test_version,test_config,test_gatekeeper}.py`.
6. Validated everything: `python -m pytest` → 15/15 passed, 97.84% coverage (gate is ≥85%); `python -m ruff check` → found 5 warnings (enum base class should be `StrEnum` not `(str, Enum)`; `Callable` should come from `collections.abc`; exception name needed an `Error` suffix) — fixed all 5, re-ran to confirm 0 warnings. All files confirmed ≤150 lines (largest is `gatekeeper.py` at 87).
7. Wrote the root `README.md` to the full academic/user-manual standard required by both PDFs, including the Dec-POMDP tuple mapping and an honest, non-inflated implementation-status table.
8. Updated `docs/TODO.md` and `docs/01_requirements_matrix.md` status columns to reflect what was actually built (not aspirationally marked done) — several SG-C0x/SG-D0x rows moved from ⬜ to ✅, `uv.lock` row stays 🟨 since `uv` itself isn't installed in this environment.

**Key decisions / lessons learned**:
- `uv` was confirmed unavailable on PATH (`uv --version` → command not found) even though PyCharm's `.idea/*.iml` references a "uv (HW6)" SDK — used plain `pip`/`python -m pytest`/`python -m ruff` only for the assistant's own local validation of the skeleton, while keeping every *committed* instruction (README, PRDs) in the mandated `uv run` form. This distinction is recorded so a future session doesn't mistake the validation method for the required workflow.
- Ran real lint/test/coverage checks rather than asserting compliance — caught and fixed real ruff violations before they could accumulate, validating the "tests/lint before claiming done" rule from the start of the project rather than retrofitting it later.
- Deliberately implemented Chunk 2 (config/version/gatekeeper) fully rather than stubbing it, since the Phase 3 instruction was "minimal import-safe placeholder code" but these three modules are small, dependency-free, and explicitly load-bearing for every later chunk — stubbing them would have meant rewriting the same interfaces twice. All game-domain code (agents/mcp/race/reporting) was correctly left as stubs since that logic is genuinely undetermined until their respective chunks/PRDs are executed.

**Next planned entry**: after Chunk 3 (MCP server layer) or whichever chunk the user approves next.

---

## Entry 3 — 2026-06-24 — Session constraints: 150-line gate, autonomous mode, PRD catalog

**Prompt context/goal**: User granted standing autonomous approval for normal project work inside the HW6 folder (no need to ask permission for file/folder creation, edits, docs, tests, safe local commands) while keeping an explicit stop-list (deleting large parts of the project, deleting the PDFs, touching files outside HW6, installing unusual global tools, system files, permanent env vars, secrets/API keys, GitHub pushes, unnecessary network calls, or implementing a requirement in a way that conflicts with the PDFs). Before continuing to Chunk 3, the user asked for two new strict project rules to be documented and tooled: (1) a 150-physical-line cap on every Python file, with automated validation; (2) at least 510 PRDs, organized as a numbered catalog under `docs/prds/catalog/` with an index, covering HW/Guidelines/architecture/implementation-level detail without being meaningless filler.

**What was done**:
1. Added `tests/test_line_limits.py` — scans `src/`, `tests/`, `tools/` for `*.py` files and asserts each is ≤150 *physical* lines (blank/comments counted), stricter than the Guidelines PDF's logical-line cap. Confirmed passing against the existing codebase (largest file: `shared/gatekeeper.py` at 87 lines).
2. Documented the rule as ADR-006 in `docs/PLAN.md`, as `PROJ-R01`/`PROJ-R02` in `docs/01_requirements_matrix.md`, and as a new §9a in `docs/00_source_analysis.md` ("session-level project rules — not from either PDF, but binding") — explicitly distinguishing these from PDF-sourced requirements so traceability stays honest.
3. Built the 510+ PRD catalog **without hand-writing 510 files**: wrote a one-off data-harvesting script (run from scratchpad, not tracked in the repo) that parsed real project artifacts — `docs/01_requirements_matrix.md`'s 59 rows, `docs/06_submission_checklist.md`'s 38 checklist lines, both `config/*.json` files' keys, the 12 chunks' 8 attributes each in `docs/04_implementation_chunks.md`, plus curated (not randomly generated) lists covering modules, JSON schema fields, CLI behaviors, error cases, logging requirements, validation rules, architecture decisions, packaging items, ISO 25010 characteristics, parallelism guidance, git workflow, bonus-round rules, LLM connectivity options, Nielsen heuristics, component I/O/Setup documentation, doc-currency items, and ~60 concrete test-case specifications — totaling **522 items**, comfortably over the 510 minimum, with zero filler/random entries.
4. Wrote the small, tracked generator `tools/generate_prd_catalog.py` (≤150 lines, itself subject to the new line-limit rule) that reads `tools/prd_catalog_data.json` and renders `docs/prds/catalog/PRD-0001.md`..`PRD-0522.md` plus `docs/prds/PRD_INDEX.md` (grouped by 21 categories) — kept the data separate from the generator specifically so the generator script could stay small and re-runnable.
5. Updated `docs/04_implementation_chunks.md` with a blanket project-rule note plus a per-chunk amendment to every "Done criteria" line referencing `tests/test_line_limits.py`.
6. Updated `docs/06_submission_checklist.md` with a new "§F. Project-specific session constraints" section covering the line-limit check, PRD-count check, and tests-pass check.
7. Caught and fixed staleness in `docs/TODO.md`: several Phase 0 rows had been left at `not-started` even though the corresponding docs were actually completed in Entry 1/2 — corrected to `done` rather than letting the discrepancy stand, consistent with the project's own "no doc drift" rule (SG-D05).
8. Re-ran the full gate after all changes: `pytest` → 38/38 passed, 97.84% coverage; `ruff check src/ tests/ tools/` → 0 warnings; `tests/test_line_limits.py` → all files pass.

**Key decisions / lessons learned**:
- Treated "≥510 PRDs, not meaningless" as a hard constraint to satisfy with *real* derived content rather than templated nonsense — every catalog entry traces to an actual file, config key, requirement ID, checklist line, or concretely-named test case, never a generic placeholder.
- Kept the bulk PRD *data* out of any tracked `.py` file specifically because the new 150-line rule applies to `tools/**/*.py` too — a single large script would have either violated the rule or required artificial fragmentation; externalizing to JSON was the cleaner solution and also makes the catalog easy to regenerate/extend later via `uv run python tools/generate_prd_catalog.py`.
- No real game/MCP/agent logic was implemented in this session, per explicit instruction ("implement real project logic" was out of scope) — only documentation, tooling, and validation infrastructure.

**Next planned entry**: after Chunk 3 (MCP server layer) is implemented.

---

## Entry 4 — 2026-06-24 — Chunk 3: MCP server/client layer

**Prompt context/goal**: User confirmed standing autonomous approval and asked to continue to Chunk 3 (PRD-002: MCP server/client layer) — the two independent FastMCP servers (Cop, Thief) with token-based auth + revoke, satisfying HW-F13/F14/F15/F17/F18.

**What was done**:
1. Verified `fastmcp` (3.4.2) was already importable in this environment; inspected its real API (`FastMCP`, `Client`, `@app.tool`, `fastmcp.exceptions.ToolError`) via small throwaway scripts before writing any production code, including a smoke test proving `Client(app)` works fully in-process against a `FastMCP` instance with no real sockets — this directly enables PRD-002's "no real network sockets in unit tests" requirement.
2. Designed the tool surface as fully symmetric between Cop and Thief (`send_message`, `receive_message`, `get_inbox`), deliberately deferring all game-specific tool shaping to Chunk 4/6 — consistent with PRD-002's stated scope ("this chunk's tools pass natural-language text through; they do not interpret or validate game legality"). This let `server_a.py`/`server_b.py` become trivial ~17-line instantiations of one shared builder (`server_base.py`), so there is exactly one place auth and tool-registration logic exists (SG-C04 — zero duplication).
3. Implemented `services/mcp/{auth.py, message_store.py, server_base.py, server_a.py, server_b.py, client.py}` — `auth.py`/`message_store.py` are plain Python with zero FastMCP dependency, specifically so they stay trivially unit-testable; `server_base.py` is the only module that touches FastMCP's tool-registration API.
4. Installed `pytest-asyncio` locally (already a declared dev dependency in `pyproject.toml`) and added `asyncio_mode = "auto"` to `[tool.pytest.ini_options]` so async integration tests didn't need per-test markers.
5. Wrote unit tests for `auth.py` (valid/unknown/empty/revoked/wrong-role/expired/re-registered tokens, using the existing `fake_clock` fixture from Chunk 2) and `message_store.py` (send/receive/drain ordering, drain isolation, defensive copy of the outbox log), plus an integration test suite (`tests/integration/test_mcp_layer.py`) proving: messages round-trip unmodified between the two real (in-process) servers, the servers share no in-process state, invalid/revoked/wrong-role tokens are all rejected, and `get_inbox` drains rather than re-delivers.
6. Validated: 66/66 tests pass (19 new), 98.79% total coverage (100% on every new MCP module), 0 ruff warnings across `src/`, `tests/`, `tools/`, all new files well under the 150-physical-line cap (largest: `server_base.py` at 66 lines).
7. Updated `docs/TODO.md` (Chunk 3 → done) and `docs/01_requirements_matrix.md` (HW-F13/F14 → ✅; HW-F15/F18 → 🟨 since the orchestrator-as-client and real cloud URLs are later chunks; HW-F17 → ✅ for the local/auth proof, noting firewall/cloud rules apply at deploy time; SG-C12 → ✅ since FastMCP's native async model satisfies the I/O-bound concurrency guidance with no extra threading code needed). Updated 13 PRD-catalog entries' `status` fields from "Not Started" to "Done" in `tools/prd_catalog_data.json` and regenerated the catalog.

**Key decisions / lessons learned**:
- Resisted the temptation to give Cop a richer tool set (e.g., a dedicated `place_barrier_notice` tool) than Thief at this chunk, even though PRD-002's original draft suggested it — the HW PDF doesn't mandate specific tool names, and keeping the transport layer symmetric is what made zero-duplication trivial to achieve. Barrier semantics belong to the race engine (Chunk 5), not the transport layer.
- Confirmed empirically (not assumed) that FastMCP supports fully in-process client/server testing before committing to it as the testing strategy — avoided a likely false assumption that real sockets would be required.

**Next planned entry**: after Chunk 4 (agent abstraction layer) or whichever chunk is approved next.

---

## Entry 5 — 2026-06-24 — Chunk 4: Agent abstraction layer

**Prompt context/goal**: User said "continue" — proceeded to Chunk 4 (PRD-004's agent-side scope + PRD-003's DecisionStrategy interface): the LLMClient interface, DecisionStrategy interface + HeuristicStrategy, BaseAgent, and the CopAgent/ThiefAgent concrete classes, satisfying HW-F02/F15/F19 and SG-C04.

**What was done**:
1. Defined `services/agents/models.py` (`ActionType`, `AgentAction`, `AgentObservation`, `Inference`) as the one shared data contract every strategy/agent/future-race-engine module will reuse — written now specifically so Chunk 5 doesn't redefine an equivalent type later (proactive SG-C04 compliance).
2. Implemented `llm_client.py`'s `LLMClient` interface + `GatekeptLLMClient`, which routes every `generate()` call through Chunk 2's `ApiGatekeeper` — proving HW-F19's "swap provider via config/constructor, not code" property directly in a test (`test_swapping_complete_fn_requires_no_change_to_generate`).
3. Implemented `strategies/base.py`'s `DecisionStrategy` ABC and `strategies/heuristic_strategy.py`'s `HeuristicStrategy` — a deliberately deterministic, RNG-free default (fixed direction priority order, first in-bounds move wins) so tests never flake and so the "always returns a legal action" property (a named test case in `docs/05_testing_strategy.md`) is exactly and exhaustively checkable.
4. Implemented `base_agent.py`'s `BaseAgent` with `decide_action`/`compose_message`/`interpret_message`, using a Template Method hook (`_role_specific_instructions`) so `CopAgent` (mentions remaining barriers in its prompt) and `ThiefAgent` (no override needed) share 100% of their logic otherwise — directly satisfying SG-C04's "use Template Method instead of duplicating with light variations" guidance from the Guidelines PDF.
5. Designed `interpret_message` to ask the LLM to reply in a constrained `"ROW,COL"` or `"UNKNOWN"` format and parse defensively: empty opponent text short-circuits without even calling the LLM (verified by asserting the fake LLM's `prompts_seen` stayed empty); LLM exceptions and unparseable responses both degrade to a typed `Inference` (`confidence="error"`/`"ambiguous"`) rather than raising — directly satisfying the PRD-004 edge case "agent's LLM returns unparseable text → fall back gracefully, never crash."
6. Added a reusable `FakeLLMClient` test double (`tests/conftest.py`, via a `fake_llm_client_factory` fixture) supporting canned responses or a configured exception, plus `asyncio_mode = "auto"` carried over from Chunk 3 needed no changes here.
7. Wrote 32 new tests across `test_models.py`, `test_llm_client.py`, `test_strategies/test_heuristic_strategy.py` (including a parametrized "always legal" property check and the documented 1x1-grid fallback edge case), `test_base_agent.py`, `test_cop_agent.py`, `test_thief_agent.py`. All passed on the first run.
8. Validated: 112/112 tests pass, 99.20% coverage (100% on every new agent module except one already-tested fallback line), 0 ruff warnings, largest new file 88 lines (`base_agent.py`), well under the 150-line cap.
9. Updated `docs/TODO.md` (Chunk 4 → done), `docs/01_requirements_matrix.md` (HW-F02/HW-F19 → 🟨 — interface-level done, real deployment/race-engine wiring is later chunks; SG-C04 → ✅), and 13 PRD-catalog entries' statuses, then regenerated the catalog.

**Key decisions / lessons learned**:
- Deliberately kept `HeuristicStrategy` RNG-free even though "random or chosen as strategy" starting positions are allowed elsewhere (HW-Q07) — determinism in the *decision* strategy (as opposed to *starting position* randomness, which belongs to Chunk 5's race engine) makes this layer's tests exact rather than statistical, which is the simpler and equally valid choice for a default that's explicitly not meant to be clever (HW-F03: orchestration is graded, not strategy).
- Used the real "no test depends on a live external service" rule literally: every test in this chunk uses a fake LLM client; no API key, network call, or real provider SDK was touched.

**Next planned entry**: after Chunk 5 (dual-agent race mechanism) or whichever chunk is approved next.

---

## Entry 6 — 2026-06-24 — Chunk 5: Dual-agent race mechanism

**Prompt context/goal**: User said "continue" — proceeded to Chunk 5 (PRD-003): the grid/race engine — `RaceState`, `RaceEngine`, `scoring.py`, satisfying HW-F04/F05/F06/F07/F08/F09/F10/F11/F25.

**What was done — and an important self-correction**:
1. Before writing any code, re-derived the exact arithmetic behind HW-F11's "max 90 / min 30 points per group per full game" claim, to make sure tests would assert the right thing. Discovered that for a *fixed-role* local match (the only kind Chunk 5/6 can test — one agent always Cop, the other always Thief across all 6 sub-games), the actual provable bound is `cop_total ∈ [30,120]`, `thief_total ∈ [30,60]` — the literal PDF "90/30" figure only arises under a 3-Cop-role + 3-Thief-role split, which the HW PDF only explicitly describes for the inter-group bonus round (HW-F27, §12.1). This meant my own **earlier** documentation (written in the Chunk 0/1 planning session) had baked in a wrong assumption — `docs/prds/PRD-003-dual-agent-race-logic.md`'s acceptance criteria and `docs/04_implementation_chunks.md`'s Chunk 5 "Expected output" both asserted the literal 90/30 bound applied to local matches. Fixed both files with the corrected derivation, and added `HW-Q08` to `docs/07_risks_and_open_questions.md` flagging that the *true* answer (does a single local "game" swap Cop/Thief roles partway, like the bonus round does?) still needs user confirmation before Chunk 7's reporting is finalized — the race engine itself is written role-agnostically so it's correct either way, only the reporting *framing* depends on the answer.
2. Implemented `services/race/exceptions.py` (`IllegalMoveError`, `IllegalActionError`), `models.py` (`SubGameResult`, `GameResult`, reusing `AgentAction`/`ActionType` from Chunk 4 rather than redefining them), `scoring.py` (pure config-driven lookup), `race_state.py` (`RaceState`: bounds checking, one-way Cop-only barriers, capture/survival win conditions), and `race_engine.py` (`play_sub_game`/`play_game`, decoupled from any agent/LLM/strategy — pure `(RaceState) -> AgentAction` policy callables).
3. Made and documented three interpretation decisions explicitly (all already anticipated as open items in PRD-003's "Edge Cases" section from the planning session): (a) "25 moves" is a *total* count shared by both agents, not per-agent; (b) a same-cell start is an immediate Cop win at move 0; (c) capture is checked after *either* agent's move landing on the same cell, not only a Cop-initiated capture, since the HW PDF only describes the Cop's case but the physical state is identical either way.
4. While writing the `play_game` aggregation test, caught a second, more local bug in my own test design before it became a flaky test: reusing a single stateful `itertools.cycle`-based policy object across multiple sub-games breaks because each Thief-win sub-game consumes an *odd* number of Thief calls (13, since Thief moves first and the 25th total move is always a Thief move) — so a 2-element cycle's phase silently drifts between sub-games and can produce an illegal first move into a wall. Fixed by switching the THIEF_WIN test policies to stateless functions that recompute the right oscillating direction purely from the current `RaceState` position (the same pattern a real `DecisionStrategy` already uses) — this is both correct and a more realistic test double.
5. Wrote 35 new tests (18 `race_state`, 4 `scoring`, including a "literal HW PDF example" test that the 4-Cop-win/2-Thief-win split exactly reproduces the example's `totals: {cop: 90, thief: 40}` from the HW PDF, plus 5 `race_engine` tests). All passed; fixed one ruff warning (`dict()` call → literal) found on the first lint pass.
6. Validated: 147/147 tests pass, 99.39% coverage (100% on every new race module), 0 ruff warnings, largest new file 90 lines (`race_state.py`).
7. Updated `docs/TODO.md` (Chunk 5 → done, noting Q-Learning stretch not attempted), `docs/01_requirements_matrix.md` (HW-F07/F08/F09/F10/F11 → ✅; HW-F04/F05 → 🟨 since orchestrator wiring and JSON reporting are later chunks; SG-C13 → 🟨 progressing), 23 PRD-catalog entries, and regenerated the catalog.

**Key decisions / lessons learned**:
- This is the second time in this project that writing the actual code/tests surfaced an error in documentation written *before* any code existed — reinforces why `docs/07_risks_and_open_questions.md` exists as a living document rather than a one-time planning artifact, and why "no vibe coding" doesn't mean "docs are infallible," only that code shouldn't improvise *past* what the docs say without updating them when they're found to be wrong.
- Kept the race engine fully decoupled from `services/agents` (only `services/agents/models` is imported, for the shared `AgentAction`/`ActionType` types) — confirmed this boundary holds by writing every Chunk 5 test against plain callables, never against `BaseAgent`/`DecisionStrategy` instances.

**Next planned entry**: after Chunk 6 (controller/orchestrator) or whichever chunk is approved next.

---

## Entry 7 — 2026-06-24 — Chunk 6: Controller / orchestrator / game loop

**Prompt context/goal**: User said "continue" — proceeded to Chunk 6 (PRD-004's orchestrator half): `Hw6RaceSDK.run_local_match()` tying together Chunks 3 (MCP), 4 (agents), 5 (race engine) into one runnable match, satisfying HW-F01/F02/F15 and SG-C03.

**What was done**:
1. Made an architecture decision before writing code, recorded as ADR-007 in `docs/PLAN.md`: rather than making the already-finished, tested `race_engine.play_sub_game`/`play_game` async (or bridging via a wasteful per-call `asyncio.run()`), wrote a new async turn loop directly in `sdk/orchestrator.py` that holds MCP client connections open for a whole match, while still reusing `RaceState`/`score_sub_game`/`GameResult` directly with zero duplication of scoring/legality logic. Documented the accepted trade-off (the thief-then-cop alternation *shape* now exists in two places) explicitly rather than silently.
2. Split the work into three files to respect the 150-line cap from the start: `sdk/wiring.py` (constructs agents/auth/servers/clients, including a deliberately safe **no-network default LLM stub** — this project must never make a real API call without the user supplying real credentials), `sdk/orchestrator.py` (the async turn loop: `observation_for`, `take_turn`, `play_sub_game_async`, `play_game_async`), and a rewritten `sdk/sdk.py` (the thin public facade, bridging the sync public API to the async internals via `asyncio.run()`).
3. Verified there was no circular-import hazard from `sdk/sdk.py` importing sibling submodules `orchestrator`/`wiring` while `sdk/__init__.py` is mid-import — tested empirically (`from hw6_race.sdk import Hw6RaceSDK` succeeds) rather than assumed.
4. **Ran a real, full end-to-end smoke test before writing any formal tests**: `Hw6RaceSDK().run_local_match()` against the actual default 5×5/6-sub-game config. It completed successfully — 6/6 sub-games, all `COP_WIN` at move 16, `cop_total=120`/`thief_total=30` — which is exactly the `w=6` (all-Cop-wins) edge of the bound derived in Chunk 5 (`cop_total=15w+30`, `thief_total=60−5w`), a nice independent confirmation that both the Chunk 5 math and the Chunk 6 wiring are correct together. The run also triggered the local LLM-call rate limit partway through (the default "llm" service allows 20/min, and a full match makes hundreds of compose/interpret calls) — `BaseAgent` degraded gracefully every time (logged, fell back to "no comment"/"UNKNOWN", never crashed), which is exactly PRD-004's required edge-case behavior, observed live rather than only asserted in a mock.
5. Implemented Technical-Loss containment in `play_game_async`: a sub-game that raises is caught and recorded via the existing `score_sub_game(GameOutcome.TECHNICAL_LOSS, ...)` path rather than crashing the whole match — explicitly documented as *not* yet including Chunk 7's rerun-to-exactly-6-completed-sub-games bookkeeping.
6. Wrote 19 new tests across `test_wiring.py`, `test_orchestrator.py` (observation/turn-level, using hand-written fake agent/MCP-client doubles), `test_play_sub_game_async.py` (capture-breaks-the-loop and Technical-Loss-containment cases), `test_sdk.py`, and an integration suite (`test_orchestrator_integration.py`) that builds real in-process MCP servers with explicit `MessageStore` instances so the test can assert messages actually flowed through the MCP layer (not bypassed), plus a full-default-config `Hw6RaceSDK` smoke test.
7. Caught and fixed a self-inflicted line-limit violation: after adding the Technical-Loss/capture-break tests, `test_orchestrator.py` grew to 153 lines. Rather than requesting an exception, split the shared fake-agent/fake-MCP-client test doubles into `tests/unit/test_sdk/_orchestrator_doubles.py` and split the tests themselves into `test_orchestrator.py` (observation/turn-level) and `test_play_sub_game_async.py` (sub-game/match-level) — exactly the "split into smaller modules" response the project's own rule (PROJ-R01) prescribes.
8. Validated: 173/173 tests pass, **100% coverage** (every line of every new module exercised, including the previously-uncovered capture-break and Technical-Loss branches), 0 ruff warnings (fixed one import-sort issue via `ruff check --fix`), all files ≤111 lines (`orchestrator.py`).
9. Updated `docs/TODO.md` (Chunk 6 → done), `docs/01_requirements_matrix.md` (HW-F01/F02/F04/F15/SG-C03 → ✅; HW-F05/HW-N01-06 → 🟨, correctly deferred to Chunk 7/10), 10 PRD-catalog entries, and regenerated the catalog.

**Key decisions / lessons learned**:
- Running the real end-to-end smoke test *before* writing the formal test suite (rather than only writing tests against mocks first) caught the realistic rate-limit interaction early and turned it into a positive validation of the Gatekeeper + graceful-degradation design, instead of a surprise discovered later.
- Reused the project's own documented self-correction discipline a third time in two chunks: caught my own line-limit violation immediately after introducing it and split the file rather than letting it slide "just this once."

**Next planned entry**: after Chunk 7 (logging, JSON protocol, reporting) or whichever chunk is approved next.

---

## Entry 8 — 2026-06-25 — Process change + Chunk 7: reporting/JSON/email

**Prompt context/goal**: Mid-Chunk-7, the user interrupted to set a new standing process rule: commit and push to `github.com/AliTrabeh/dual-agent-race-mcp` after **each** completed chunk, not all together at the end, and explicitly work one chunk at a time rather than chaining several. Confirmed this, set up git (the folder was not yet a repo), verified push auth worked via Windows Credential Manager (no `gh` CLI available in this environment), and pushed a single catch-up commit covering Chunks 0–6 (with the one half-written Chunk 7 file removed first, since it wasn't finished) before resuming Chunk 7 properly from a clean state.

**What was done (Chunk 7 itself, PRD-005)**:
1. Implemented `services/reporting/schemas.py` (`InternalGameReport`, `build_sub_games_payload`) and `bonus_report.py` (`InterGroupBonusReport`, `compute_bonus_claim`) — both verified field-for-field against the HW PDF's literal JSON examples (HW-F23/F24), not just "close enough."
2. Implemented `technical_loss.py`'s `resolve_technical_losses` as a clean, fully tested, standalone algorithm (replace failed sub-games with reruns up to a max-attempts cap) — but made a deliberate, explicitly documented decision **not** to wire it into a single live match's MCP-client-connection scope this chunk, after recognizing that doing so safely would require either reusing FastMCP clients after their async context had already exited (behavior not verified) or accepting a third near-duplicate of the per-sub-game loop shape beyond the two already accepted in ADR-007. Recorded this as a flagged "Known limitation" in `docs/07_risks_and_open_questions.md` rather than quietly shipping a fragile wiring attempt or silently dropping the requirement.
3. Implemented `run_logger.py`'s `RunLogger` as an incremental accumulator (`record()` + `build_report()`), matching PRD-005's original framing ("accumulates... as a match progresses") more faithfully than a simple "wrap a finished GameResult" function would have.
4. Implemented `mailer.py`'s `ReportMailer`, routed through the same `ApiGatekeeper` as LLM calls (SG-C05 consistency) — the email body is always exactly `json.dumps(report)`, enforced by being the only function in the codebase allowed to construct an outbound email (HW-F22's "JSON only, no free text" rule).
5. Wrote 20 new tests (`test_schemas.py`, `test_bonus_report.py`, `test_technical_loss.py`, `test_run_logger.py`, `test_mailer.py`) — all mailer tests use a fully mocked `send_fn`; no real Gmail call is made anywhere in the suite.
6. Validated: 203/203 tests pass, **100% coverage** maintained, 0 ruff warnings, largest new file 77 lines (`schemas.py`).
7. Updated `docs/TODO.md` (Chunk 7 → done, with the known limitation noted), `docs/01_requirements_matrix.md` (HW-F05/F23/F24/F28 → ✅; HW-F21/F22 → 🟨, correctly reflecting the Gmail-credentials and rerun-wiring gaps), 40 PRD-catalog entries, and regenerated the catalog.

**Key decisions / lessons learned**:
- This is the clearest example yet in this project of choosing honesty over the appearance of completeness: `resolve_technical_losses` works and is tested, but admitting it isn't *wired in* yet — rather than bolting on a risky integration just to mark the box fully checked — is the behavior the project's own process rules (SG-D05, "keep docs current," and the running self-correction pattern from Chunks 5/6) are there to produce.
- Adopted the user's new per-chunk commit/push cadence starting with this chunk; this entry's corresponding commit is the second one pushed to the repo.

**Next planned entry**: after Chunk 8 (CLI interface) or whichever chunk is approved next.

---

## Entry 9 — 2026-06-25 — Chunk 8: CLI interface

**Prompt context/goal**: User said "continue chunk 8" — proceeded to the CLI interface (`main.py`): argument parsing, calling only `Hw6RaceSDK`, pretty-printing results, satisfying SG-C03.

**What was done**:
1. Before writing the CLI, re-checked Chunk 6's own plan and found a real gap: its Steps explicitly listed "4) full per-turn trace logging," but Chunk 6 had only added DEBUG-level inference logging — no INFO-level log of what an agent actually composed or decided each turn. Fixed this retroactively in `sdk/orchestrator.py`'s `take_turn` (two new `logger.info` calls: composed message + decided action), re-ran the full Chunk 6/7 test suite to confirm nothing broke, then proceeded.
2. Implemented `main.py` with `argparse`: `--config`, `--dry-run`, `--log-level` (default INFO), `--output-dir`, and `--version` (using argparse's built-in `action="version"` rather than hand-rolling it, for a correctness guarantee). Kept it deliberately free of business logic — it only parses args, configures logging, calls `Hw6RaceSDK`, and formats/writes output using the *existing* `services.reporting.schemas.build_sub_games_payload` helper (no ad-hoc dict-building reinventing the report shape).
3. Ran the CLI manually end-to-end before writing tests (`--help`, `--version`, `--dry-run`, a real full match, a missing-config error case) — caught that FastMCP's own internal `mcp.server.lowlevel.server` logger was drowning out the new per-turn trace at INFO level, and fixed it by setting that specific logger to WARNING in `main()` (silencing library noise without touching the project's own log levels) — confirmed by re-running and visually inspecting the now-readable trace.
4. Defined exit-code semantics matching the PRD catalog's CLI behavior items: 0 on a clean run or dry-run, 1 on a config error or on any Technical Loss sub-game in the result.
5. Wrote 5 tests (`test_main.py`) covering arg-parser defaults, dry-run, missing-config error, a full mocked-SDK run with output-file verification, and the Technical-Loss-causes-nonzero-exit case.
6. Validated: 209/209 tests pass, 100% coverage on every module the coverage config actually measures (`main.py` is in the Guidelines PDF's own example `omit` list — by design, not an oversight — but is still tested directly), 0 ruff warnings, `main.py` at 89 lines.
7. Updated `docs/TODO.md` (Chunk 8 → done, noting the Chunk 6 trace-logging fix), `docs/01_requirements_matrix.md` (SG-C03 note extended), 18 PRD-catalog entries, and regenerated the catalog.

**Key decisions / lessons learned**:
- Retroactively closing a gap from a previous, already-"done" chunk (rather than treating "done" as immutable) is now an established pattern in this project — the chunk plan's own steps are a checklist to re-verify against, not just a one-time guide.
- Confirmed real, visible CLI output before trusting the test suite's assertions about it — the FastMCP logging-noise issue would not have been caught by a unit test using a mocked SDK, only by actually running the command.

**Next planned entry**: after Chunk 9 (suite-level test completion) or whichever chunk is approved next.

---

## Entry 10 — 2026-06-25 — Chunk 9: suite-level test completion

**Prompt context/goal**: Between Chunk 8 and Chunk 9, the user manually tried the CLI themselves (confirmed it works — 6/6 Cop wins, totals 120/30, exactly matching the deterministic stub-LLM+heuristic prediction) and asked an exploratory question about adding a browser GUI. Per the "exploratory question" guidance, gave a short recommendation (feasible, SDK boundary already supports it cleanly, but it's explicitly optional per the HW PDF) and a tradeoff, without implementing anything, then deferred it until the required chunks (9–11) are finished, per the user's explicit choice. Also fixed a one-line accidental edit to `main.py` (stray `i want t` text prepended to the docstring, breaking the syntax) before re-verifying the CLI worked. Then proceeded to Chunk 9 (PRD-006): suite-level test completion.

**What was done**:
1. Implemented `tests/integration/test_staged_sanity_checks.py`, parametrized over all 6 grid sizes the HW PDF's sanity-check table names (`2×2`, `3×3`, `3×2`, `4×4`, `4×3`, `5×5`), asserting each completes without exception, produces the right number of sub-games, every outcome is valid, and totals stay within the bound formula derived in Chunk 5. Added a dedicated Stage-1 (2×2) test that builds explicit `MessageStore` instances (same pattern as Chunk 6's integration test) to assert the message pipeline is actually lossless on the smallest grid, not just "the match completed" — directly matching HW-F12's literal wording for Stage 1.
2. Audited for coverage/lint gaps to close per PRD-006's scope — found none: coverage has been 100.00% since Chunk 6 and stayed there through Chunks 7/8, so this chunk's "suite-level completion" work was almost entirely the staged-sanity-check matrix itself rather than backfilling missed tests.
3. Updated `docs/05_testing_strategy.md` §2 to point at the now-real `tests/integration/test_staged_sanity_checks.py` instead of describing it only as planned.
4. Validated: 217/217 tests pass (7 new), 100% coverage maintained, 0 ruff warnings, new file 84 lines.
5. Updated `docs/TODO.md` (Chunk 9 → done), `docs/01_requirements_matrix.md` (HW-F12 → ✅; SG-T01–T06 → ✅, reflecting that these were actually satisfied incrementally across every prior chunk, not just now), 7 PRD-catalog entries, and regenerated the catalog.

**Key decisions / lessons learned**:
- This chunk confirmed something worth naming explicitly: because every previous chunk insisted on hitting 100% coverage and 0 ruff warnings *before* moving on, Chunk 9's "catch-up" scope shrank to almost nothing — the discipline paid for itself rather than deferring cost to a big cleanup pass at the end.
- Caught the user's accidental file edit before it could cause confusion later (a stray prepended string would have caused a `SyntaxError` on the next run) — flagged it plainly and fixed it as a one-line, surgical edit rather than rewriting the file.

**Next planned entry**: after Chunk 10 (documentation finalization & submission packaging) or whichever chunk is approved next.

---

## Entry 11 — 2026-06-26 — Permissions config + Chunk 10: documentation finalization

**Prompt context/goal**: Between chunks, the user pasted `{"permissions": {"defaultMode": "bypassPermissions"}}` asking to apply it. Invoked the `update-config` skill; discovered the project's `.claude/settings.local.json` is auto-rewritten by the harness every time a Bash permission is recorded, which clobbered the `defaultMode` edit twice before it could persist. Resolved by creating a separate `.claude/settings.json` (not subject to that auto-append behavior) with just the requested key, scoped to this project only — explicitly avoided writing it to the *global* `~/.claude/settings.json`, since the user's standing instruction was scoped to this project, not all their Claude Code projects. Flagged for the user that this file is the committed/team-shared one (will be pushed to GitHub) in case they'd prefer it untracked. Then proceeded to Chunk 10 (PRD-007): documentation finalization & submission packaging.

**What was done**:
1. Scoped Chunk 10 honestly before starting: real cloud deployment requires a cloud account/credentials this session does not have and should not fabricate, so the chunk's deliverable was redefined as (a) a fully finalized scientific README, (b) an actionable, step-by-step cloud deployment *guide* — not a performed deployment, (c) a real fresh-clone smoke test (genuinely achievable without external credentials), and (d) an honest update to the submission checklist distinguishing what's done from what's externally blocked.
2. Found and fixed substantial staleness in `README.md` accumulated across 9 prior chunks of incremental edits: the top banner still said "Game logic implementation has not started yet" (false since Chunk 6), §5's test-count sentence had become a garbled merge of two different edits from different chunks, and §7's intro paragraph and §11's closing summary both still said "pending chunks 3–10" for things that had been done since Chunk 6.
3. Rewrote the README in full: added §2 "The Orchestration Challenge (Theoretical Discussion)" — a real academic-style discussion of the three concrete consequences of the HW PDF's "no rigid protocol" constraint (no schema → can't use the MCP layer as a side channel; ambiguity is the default → `interpret_message`'s three-way degradation path; no referee for mutual understanding → why capture-checking is symmetric in `RaceState`) — and §5 "CLI Run Evidence" using an actual freshly-captured run's output (not reconstructed from memory), explicitly noting the realistic rate-limit-driven `WARNING ... UNKNOWN` lines as evidence of graceful degradation working live. Added §8 "Deployment Guide: Local → Cloud → Inter-Group Bonus" as concrete, numbered, actionable steps for stages this session cannot perform.
4. Caught and fixed a section-numbering bug (duplicate `## 9.`) introduced while writing the new sections, before it shipped.
5. Rewrote `docs/06_submission_checklist.md` with every item marked exactly as true/false/N/A — including a new §G "Summary of remaining gaps" table naming each open item, why it's open, and whether it's actually submission-blocking. Explicitly checked the box for "git history meaningful" but **left "feature branches + PRs + release tags" unchecked**, naming directly that this project has committed straight to `main` per the user's own explicit per-chunk workflow request — a real, acknowledged process gap, not glossed over for the sake of a clean checklist.
6. Validated: 217/217 tests still pass, 100% coverage, 0 ruff warnings (no production code changed this chunk, only docs).
7. Updated `docs/TODO.md` (Chunk 10 → "done (with honest gaps)"), `docs/01_requirements_matrix.md` (HW-F26/SG-D01 → ✅; HW-F16 → 🟨 with the 3 stages' real individual status spelled out), 25 PRD-catalog entries, and regenerated the catalog.

**Key decisions / lessons learned**:
- Treated "finalize documentation" as an opportunity to audit for drift, not just add new content — three separate stale claims in the README would have actively misled a reader if left as-is, and catching them now (rather than at a hypothetical future "final polish" pass) is consistent with this project's running theme of fixing documentation debt as soon as it's found.
- Deliberately wrote the submission checklist's gaps section to be *useful*, not just honest — each gap states why it's open and whether it actually blocks submission, so the user can make an informed call about priority rather than just seeing a wall of unchecked boxes.

**Addendum — fresh-clone smoke test caught a real bug**: per PRD-007's acceptance criteria, ran an actual fresh-clone smoke test — cloned the just-pushed commit into an isolated scratchpad directory and ran `uv sync` → `uv run pytest --cov` → was about to run the CLI. `uv sync` succeeded and all 217 tests passed, but coverage reported a suspicious **0.00%** instead of the expected 100%, with a `CoverageWarning: No data was collected`. Root cause: `pytest`/`pytest-cov`/`ruff` were declared under `[project.optional-dependencies] dev = [...]`, which `uv sync` does **not** install by default (only `[dependency-groups]` get installed automatically) — so in a genuinely clean environment, `uv run pytest`/`uv run ruff check` would not actually be runnable at all. The reason this had not been caught in 9 prior chunks of "validated via `uv run`" claims is that *this development machine* had a leftover global `pytest`/`coverage` installation from this session's own earlier `pip install` debugging (before `uv` was confirmed working in Chunk 9) — `uv run` silently fell through to that global installation on PATH, which happened to still import `hw6_race` successfully (via a stale global editable install) but couldn't resolve `--cov=src` correctly, producing passing tests with bogus 0% coverage rather than an outright failure. Fixed by switching `pyproject.toml` to `[dependency-groups] dev = [...]` (the uv-idiomatic form, installed by `uv sync` automatically), regenerating `uv.lock`, and re-verifying both in the real working directory and in a second fresh clone — both now show 217/217 passing, 100% coverage, 0 ruff warnings, with `uv sync` alone (no extra flags) being sufficient. This is the most consequential bug this project's testing discipline has caught precisely *because* it was invisible from inside the development machine and only surfaced via an actually-isolated clone — a strong argument for why PRD-007 specifically calls for this test rather than trusting in-place validation alone.

**Next planned entry**: after re-confirming the fresh-clone fix, or Chunk 11 (final validation), whichever the user approves next.

---

## Entry 12 — 2026-06-26 — Chunk 11: final validation against both PDFs

**Prompt context/goal**: User said "continue" — proceeded to Chunk 11, the last chunk in the original plan: a final audit walking `docs/01_requirements_matrix.md` row by row against actual current repo state, re-running every gate, and either closing or honestly documenting every remaining gap.

**What was done**:
1. Re-ran the full gate first, as the foundation for the audit: 217/217 tests, 100% coverage, 0 ruff warnings, all 73 line-limit checks pass — all via the real `uv run` toolchain.
2. Walked every single row of `docs/01_requirements_matrix.md` (59 rows) against the actual current code, not against memory of what *should* be there. Found 9 rows still marked `⬜ not started` despite being genuinely done: HW-F03 (the architecture deliberately doesn't optimize win-rate — documented in README §2, never actually marked off), SG-C01/C02/C08 (line cap, docstrings/SRP/DRY, no magic values — all satisfied since early chunks but never ticked), SG-C14 (ISO/IEC 25010 self-check — never actually performed despite being referenced), SG-P02 (SDLC stage order — visibly followed the whole project), SG-U04 (Prompt Engineering Log — substantial by Chunk 10, never marked done). Fixed all 9.
3. Performed the ISO/IEC 25010 self-check that SG-C14 calls for — had been a referenced-but-never-done item until this chunk. Added `docs/06_submission_checklist.md` §H with a genuine per-characteristic assessment, each backed by a specific piece of evidence already produced earlier in the project (e.g. Portability backed by the two independent fresh-clone tests from Chunk 10, not just asserted).
4. Left `SG-U03` (git branches/PRs/tags) honestly at 🟨 rather than "fixing" it to ✅ — this is a real, acknowledged process gap (direct-to-`main` commits per the user's own workflow request), not something a final-validation pass should paper over just to make the matrix look clean.
5. Updated the canonical project-layout block at the top of `docs/01_requirements_matrix.md`, which had gone stale (still said "uv.lock generated once uv is installed" after Chunk 9 confirmed uv was installed; didn't mention `tools/` or the PRD catalog/index at all).
6. Tallied the PRD catalog's final state: 522 total, 255 Done, 240 Not Started (the bulk of which are legitimately future/external work — real cloud deployment specifics, the bonus round itself, optional Q-Learning/GUI test cases — not gaps in what was supposed to be done by Chunk 11), 17 In Progress.
7. Updated `docs/TODO.md` (Chunk 11 → done) with the exact tally and an explicit statement that no remaining gap was silently dropped.

**Key decisions / lessons learned**:
- This chunk's main value wasn't new code — it was closing the loop on a project-management discipline that's been running the whole session: several "done" items had never actually been marked done in the one document meant to be the single source of truth for grading readiness. A final audit chunk exists specifically to catch that kind of drift between "the work is done" and "the doc says so."
- Treated the ISO 25010 self-check as a real deliverable rather than a checkbox — each row in the new §H table cites a specific, already-existing piece of evidence (a test, a log entry, a prior chunk's finding) rather than a bare assertion, consistent with how every other claim in this project's docs has been handled.

**Project status at the end of Chunk 11**: all 11 originally-planned chunks are complete. The local pipeline runs genuinely end-to-end with 100% test coverage and 0 lint warnings, verified by two independent fresh clones. Remaining work — real cloud deployment, real Gmail OAuth, the inter-group bonus round, and optionally a GUI or Q-Learning strategy — all require either the user's own credentials/accounts or an external second group, and are documented as concrete next actions rather than silently incomplete.

---

## Entry 13 — 2026-06-26 — Wiring up a real LLM (Anthropic)

**Prompt context/goal**: With all 11 planned chunks done, the user asked what's next; given a choice of next steps (real LLM, cloud deploy, GUI, Gmail OAuth, bonus round, or submit as-is), they chose to wire up a real LLM first, leaning toward Claude since they already have a Claude.ai subscription. Clarified upfront — without being asked — that a claude.ai/ChatGPT *subscription* is not the same as *API access* (separate, pay-per-token billing at console.anthropic.com), and explicitly told the user not to paste the API key into the chat; they set it in `.env` themselves.

**What was done**:
1. Added `anthropic` and `python-dotenv` as real dependencies via `uv add` (not hand-edited into `pyproject.toml`), which also regenerated `uv.lock` correctly.
2. Implemented `services/agents/llm_providers.py::AnthropicCompleteFn` — a small, dependency-injectable callable (`client` param defaults to a real `anthropic.Anthropic` instance, but tests inject a fake) matching the existing `complete_fn` shape `GatekeptLLMClient` already expects, so no change was needed to the agent/Gatekeeper layers at all — exactly the pluggability HW-F19 calls for, demonstrated rather than just claimed.
3. Added `sdk/wiring.py::build_llm_client_from_env`, the one place that decides real-vs-stub: reads `LLM_PROVIDER`/`LLM_API_KEY`/`LLM_MODEL` from `os.environ`, builds a real `AnthropicCompleteFn`-backed client if both provider and key are present, and falls back to the existing safe stub otherwise — never raises, never makes an unauthorized call. Wired `Hw6RaceSDK.__init__` to call this instead of the old hard-coded stub-only builder.
4. Added `load_dotenv()` at the top of `main.py` (the CLI entry point) so `.env` is read automatically — deliberately did *not* add this to the SDK itself, keeping "read environment/bootstrap" a CLI-layer concern and the SDK importable/testable without any implicit file I/O.
5. Updated `.env-example` to document Anthropic as the implemented default provider, with a clear comment explaining the stub fallback behavior.
6. Wrote 10 new tests: `test_llm_providers.py` (response stripping, correct message shape, configured model passed through, default-to-haiku) using a fully fake injected Anthropic client — no real network call anywhere in the suite — and 3 new `test_wiring.py` cases for `build_llm_client_from_env` (unset → stub, provider-without-key → stub, fully configured → real `AnthropicCompleteFn` with the right model).
7. Validated: 226/226 tests pass, 100% coverage, 0 ruff warnings, all new/changed files well under the 150-line cap (largest: `wiring.py` at 79 lines).

**Key decisions / lessons learned**:
- Never asked for or touched a real API key directly — the user was told explicitly to manage `.env` themselves, and the integration was built and fully tested via dependency injection without ever needing a real key to exist during development.
- Confirmed the architecture's pluggability claim wasn't just aspirational: adding a second provider required exactly one new small file and one new branch in one function, with zero changes to `BaseAgent`, `CopAgent`/`ThiefAgent`, `ApiGatekeeper`, or any race/MCP code.

---

## Entry 14 — 2026-06-26 — Closing the HW-F02 gap: strategy now acts on inferred belief

**Prompt context/goal**: After confirming the real Anthropic integration worked live (the user supplied their own API key in `.env`, never shared with me), the user asked to push and then "finish it with high quality and accuracy as the requirements." HW-F02 literally requires "decode message → infer position → translate to move," but the move-decision step had been deliberately left a documented gap. Closed it properly.

**What was done**:
1. Added `role` and `believed_opponent_position` fields to `AgentObservation` (both default `None`, preserving every existing construction call site and test). `BaseAgent` now tracks a running belief, updated only on a successfully parsed position — an ambiguous/empty/error turn preserves the last known good belief rather than discarding it. `HeuristicStrategy` chases (Cop minimizes Manhattan distance) or flees (Thief maximizes it) once a belief exists, falling back to the original fixed-priority move otherwise.
2. Also tightened `BaseAgent._build_interpret_prompt` (noticed during the earlier live run that real Claude responses often padded "UNKNOWN" with unsolicited explanation, wasting tokens) — now explicitly asks for *only* the token, no explanation.
3. **Found and fixed a real, serious bug introduced by this same change**: the first full-suite run after these edits took 160 seconds instead of ~14, and showed real `HTTP/1.1 200 OK` calls to Anthropic happening *during the test run* — `tests/unit/test_main.py` imports `hw6_race.main`, and `main.py` had `load_dotenv()` at module level, so merely *importing* it during pytest collection loaded the real `.env` (with a real `LLM_API_KEY`) into `os.environ` for the rest of the session, silently making every subsequent `Hw6RaceSDK()` construction use the real backend instead of the stub — a direct violation of SG-T03 ("no test depends on a live external service"). Fixed two ways: moved `load_dotenv()` from module level into the `main()` function body (so importing the module has no side effect), **and** added an autouse `conftest.py` fixture that sets (not deletes) `LLM_PROVIDER`/`LLM_API_KEY`/`LLM_MODEL` to empty strings before every test — exploiting python-dotenv's documented `override=False` default (an *already-present*, even empty, env var is never overwritten by `load_dotenv()`), so the fix holds even for tests that call `main()` directly mid-test, not just tests that merely import the module.
4. Re-ran the full suite after the fix: back to ~14 seconds, confirming zero real network calls anywhere in the test suite.
5. Discovered the new chase/flee code path was only 55% covered (no existing test ever set a belief, since the deterministic stub never produces a parseable position) — wrote 4 new `HeuristicStrategy` tests with hand-crafted positions where chase/flee provably diverges from the default fixed-priority move, plus 3 new `BaseAgent` tests for the belief-tracking state machine (starts None, updates on success, survives a later ambiguous turn).
6. Validated live with the real LLM again: confirmed the Cop's very first inference call successfully parsed `(4, 4)` directly out of the Thief's free-text message and used it — genuine, not simulated. The match's final score happened to match the previous (stub) run's exactly, which is explained, not glossed over: chasing toward `(4,4)` from `(0,0)` ties between RIGHT and DOWN, and RIGHT wins the tiebreak, which is also what the unconditional fallback would have picked — a coincidence of this specific geometry, not a sign the logic isn't engaging (the unit tests prove correctness independently of this coincidence, using positions where the two paths provably diverge).
7. Final validation: 233/233 tests pass, 100% coverage, 0 ruff warnings, all files within the 150-line cap. Updated `docs/01_requirements_matrix.md` (HW-F02 → ✅, now citing the live-verified parse) and the README's orchestration discussion (removed the now-false claim that the strategy ignores its belief).

**Key decisions / lessons learned**:
- This is the most consequential bug caught by this project's own testing discipline since the fresh-clone `uv sync` bug in Chunk 10 — and it was caught the same way: by actually running the full suite after a change and noticing the *timing* looked wrong, not by trusting that "tests still pass" was sufficient. A test suite that's quietly hitting a real paid API is a soft failure that looks identical to success in the pass/fail output alone.
- Treated "finish it with high quality and accuracy" as license to go back and genuinely close a previously-documented, previously-justified gap, rather than treating prior "explicitly acceptable" language as permanent — the gap was acceptable *for the chunks where it was scoped that way*; once the user asked for full accuracy against the requirements, it was no longer the right call to leave it.

# PLAN — Architecture & Technical Design

> Mandatory per Guidelines PDF SG-D02. Companion to `docs/PRD.md` and `docs/03_architecture.md` (which holds the deeper narrative discussion); this file holds the structured architecture artifacts the guidelines explicitly require: C4-style diagrams, deployment diagram, ADRs, API/data docs.

## 1. C4 Model

### Context (C1)

```text
[Grader / CLI user] --runs--> [HW6 Race System]
[Cop Agent (LLM)] <--NL over MCP tools--> [Thief Agent (LLM)]
[HW6 Race System] --auto email JSON--> [Gmail: rmisegal+uoh26b@gmail.com]
[Group B's MCP servers] <--cloud HTTPS, bonus round--> [HW6 Race System]
```

### Containers (C2)

```text
+-------------------------------------------------------------+
|                      HW6 Race System                        |
|                                                               |
|  +------------------+        +------------------+            |
|  |  CLI (main.py)   |------->|     SDK          |            |
|  +------------------+        | (single entry pt) |            |
|                               +---------+--------+            |
|                                         |                     |
|        +--------------------------------+------------------+  |
|        v                  v                  v             |  |
|  +-----------+      +-----------+      +--------------+    |  |
|  | services/ |      | services/ |      |  services/   |    |  |
|  |  race     |      |  agents   |      |  reporting   |    |  |
|  +-----------+      +-----------+      +--------------+    |  |
|        ^                  |                                |  |
|        |                  v                                |  |
|        |          +---------------+                        |  |
|        +----------|  services/mcp |                        |  |
|                    +---------------+                        |  |
|                       |        |                             |
|                Cop MCP Server  Thief MCP Server              |
|                  (FastMCP)        (FastMCP)                  |
+-------------------------------------------------------------+
        |  shared/gatekeeper.py intercepts ALL outbound calls   |
        v  (LLM API calls, Gmail API calls)
   [External: LLM provider API / Ollama, Gmail API]
```

### Components (C3) — `services/mcp` (representative; see `docs/03_architecture.md` for full narrative)

- `server_base.py` — FastMCP server scaffold: auth/token verification, tool registration, ≤150 lines.
- `server_a.py` / `server_b.py` — Cop/Thief-specific tool definitions (send_message, get_position_hint), each thin, delegating logic to `services/agents`.
- MCP **Client** role is played by `sdk/sdk.py`'s race orchestrator, calling `Tool Call` against both servers and routing results to each agent's LLM client.

### Code (C4)

Deferred to actual source — kept ≤150 lines/file per SG-C01; no UML class diagram is hand-maintained ahead of code to avoid speculative design (see ADR-002).

## 2. Deployment Diagram

```text
Stage 1 (local):     localhost:8801 (Cop MCP)   localhost:8802 (Thief MCP)
                              \                          /
                               \ orchestrator (sdk.py)  /
                                \________________________/

Stage 2 (cloud):     https://cop-mcp-<group>.<host>     https://thief-mcp-<group>.<host>
                      (token-authenticated, no LLM inside the server — HW-F15/F19)

Stage 3 (bonus):      Group A's Cop MCP URL  <--cloud HTTPS-->  Group B's Thief MCP URL
                      Group B's Cop MCP URL  <--cloud HTTPS-->  Group A's Thief MCP URL
```

## 3. Architecture Decision Records (ADRs)

### ADR-001: SDK layer wraps domain services
- **Decision**: All business logic lives under `services/`; `sdk/sdk.py` is the only module CLI/tests are allowed to import from directly for behavior.
- **Rationale**: SG-C03 mandates a single entry point; keeps CLI/GUI layers logic-free and swappable.
- **Trade-off**: adds one indirection layer; acceptable given the explicit guideline requirement.

### ADR-002: No upfront UML class diagrams for code not yet written
- **Decision**: Skip hand-drawn C4-code-level / UML class diagrams until after chunk implementation; rely on docstrings (SG-C13 Input/Output/Setup) instead.
- **Rationale**: Guidelines PDF requires architecture before code, but speculative class diagrams for a system whose race/agent logic is still being designed chunk-by-chunk would violate "don't design for hypothetical requirements." We diagram containers/components (stable) but not classes (volatile).
- **Trade-off**: PLAN.md will be amended once chunks 4–6 land with the actual class shapes, per SG-D05's "keep docs current" requirement.

### ADR-003: Heuristic decision strategy first, Tabular Q-Learning as a pluggable second strategy
- **Decision**: `services/agents` defines a `DecisionStrategy` interface; ship a deterministic/heuristic implementation first (chunk 5), add `QLearningStrategy` as an additional implementation behind the same interface (stretch chunk).
- **Rationale**: HW-F20 marks Q-Learning as optional; HW-F03 says grading is about orchestration, not strategy quality.
- **Trade-off**: none significant — Strategy pattern costs little and satisfies SG-C04 (no duplicated decision logic across Cop/Thief).

### ADR-004: API Gatekeeper as a single shared singleton
- **Decision**: One `ApiGatekeeper` instance (per process) brokers all LLM API calls and the Gmail API call; rate limits loaded from `config/rate_limits.json`.
- **Rationale**: SG-C05/C06/C07 mandate this exact shape.
- **Trade-off**: Slightly more boilerplate per external call site; necessary for compliance.

### ADR-005: `uv` + `pyproject.toml` only, dropping `requirements.txt` from the user's suggested skeleton
- **Decision**: No `requirements.txt` anywhere in the repo.
- **Rationale**: SG-U01/U02 explicitly forbid it.
- **Trade-off**: None — this is a hard compliance requirement, documented in `docs/00_source_analysis.md` §9.

### ADR-007: `sdk/orchestrator.py` implements its own async per-sub-game loop, not a reuse of `race_engine.play_sub_game`
- **Decision**: Chunk 6's real MCP-integrated game loop is written as a new async function in `sdk/orchestrator.py` rather than by making `services/race/race_engine.py`'s existing synchronous `play_sub_game`/`play_game` async, or by bridging via per-call `asyncio.run()`.
- **Rationale**: FastMCP's `Client` is async, and the natural integration holds each agent's MCP client connection open for an entire sub-game/match rather than reconnecting per move. Forcing `race_engine.py` (already finished, tested, and reused as-is for non-MCP scripted testing in Chunk 5) to become async, or calling `asyncio.run()` inside every single policy invocation (~25 times per sub-game × 6), would either touch already-correct code or create dozens of short-lived event loops per match. `RaceState.apply_action`/`check_outcome` and `score_sub_game`/`GameResult` are reused directly either way — no scoring or legality logic is duplicated.
- **Trade-off**: The thief-then-cop alternation *shape* (~10 lines: call thief, check, call cop, check) now exists twice — once in `race_engine.play_sub_game` (sync, scripted-policy use) and once in `orchestrator.play_sub_game_async` (async, real-MCP use). This is judged an acceptable, minimal, well-documented exception to SG-C04 rather than a forbidden duplicated pattern: the two loops' actual statements differ substantially (one calls plain callables, the other awaits MCP/LLM I/O), and unifying them would cost more complexity than the ~10 duplicated lines save.

### ADR-006: 150-physical-line cap on every Python file (project rule, stricter than SG-C01)
- **Decision**: No file under `src/**/*.py`, `tests/**/*.py`, or `tools/**/*.py` may exceed 150 **physical** lines — counting blank lines and comments, not just logical lines. Enforced automatically by `tests/test_line_limits.py`, which is part of the standard test run.
- **Rationale**: User-specified project constraint (session instruction), layered on top of the Guidelines PDF's own SG-C01 (≤150 logical lines, excluding blank/comments). The physical-line count is the stricter of the two, so satisfying ADR-006 always satisfies SG-C01.
- **Trade-off**: Forces earlier, more aggressive modularization (helper modules, mixins, constants extraction) than SG-C01 alone would require. Accepted explicitly per user instruction — refactor early once a file approaches ~120 lines rather than waiting for the hard 150 cutoff.

## 4. API & Data Model Notes

- Internal Game JSON and Inter-Group Bonus JSON schemas are reproduced verbatim in `docs/00_source_analysis.md` HW-F23/F24 and will be implemented as typed dataclasses/`TypedDict`s in `services/reporting/schemas.py` — no hand-rolled dict building at call sites (avoids duplication, SG-C04).
- `config/setup.json` and `config/rate_limits.json` schemas are defined in `docs/01_requirements_matrix.md` and reproduced literally from the Guidelines PDF (rate limits) and HW PDF (game params).

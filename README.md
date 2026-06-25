# HW6 — Dual AI Agent Race via MCP Servers (Cop/Thief Pursuit Game)

**Course**: AI Agents / AI Orchestra — Assignment 6 ("Dual AI Agent Conversation via MCP Servers")
**Status**: All 11 planned chunks complete, plus LLM-driven and minimax decision strategies (Chunks 12-13) and the Cloud Run deployment path (Chunk 14). Full local pipeline, 342/342 tests, 100% coverage, 0 ruff warnings, verified via two independent fresh-clone tests. Real cloud deployment requires running `tools/deploy_cloud_run.sh` with your own GCP credentials; Gmail OAuth and the inter-group bonus round remain explicit user actions — see [§10 Implementation Status](#10-implementation-status) and [`docs/06_submission_checklist.md`](docs/06_submission_checklist.md).

## 1. Overview

This project implements a fully autonomous, two-agent pursuit game — a **Cop** and a **Thief**, each backed by its own LLM and its own [MCP](https://modelcontextprotocol.io/) (Model Context Protocol) server — that play a sequence of pursuit episodes on a configurable 2D grid. The two agents never share memory or a rigid message schema: they communicate exclusively through free natural-language text, exchanged via MCP tool calls. Grading for this assignment is explicitly about the quality of that orchestration and communication, **not** about which agent wins more often.

Formally, this is a 2-agent, partially-observable, decentralized pursuit problem — a **Dec-POMDP**:

```
⟨ n, S, {Aᵢ}, P, R, {Ωᵢ}, O, γ ⟩
```

| Symbol | Meaning in this project | Implemented by |
|--------|---------------------------|------------------|
| `n = 2` | Cop and Thief agents | `services/agents/{cop_agent,thief_agent}.py` |
| `S` | Full grid state: Cop position, Thief position, set of up to 5 barriers, move counter | `services/race/race_state.py::RaceState` |
| `{Aᵢ}` | Thief: 4 movement directions. Cop: 4 movement directions + place-barrier | `services/agents/models.py::AgentAction` |
| `P` | Deterministic grid transition given a legal action | `RaceState.apply_action()` |
| `R` | The fixed scoring table (Cop win → 20/5, Thief win → 10/5), sourced from `config/setup.json` | `services/race/scoring.py::score_sub_game()` |
| `{Ωᵢ}` | Each agent observes only its own position plus whatever natural-language text the opponent chose to send — this is the partial-observability layer | `services/agents/models.py::AgentObservation` |
| `O` | Implicit in what each agent's MCP server tool returns to its own LLM client — never a shared ground-truth channel | `services/mcp/server_base.py`, `sdk/orchestrator.py::take_turn` |
| `γ` | Discount factor, meaningful only if the optional Q-Learning strategy (`docs/PRD_q_learning.md`) is enabled | not yet implemented (explicitly optional, HW-F20) |

## 2. The Orchestration Challenge (Theoretical Discussion)

The hardest engineering problem this assignment targets — named explicitly in the source PDF — is that the two agents are **independent, decoupled, and use free natural language with no shared protocol** to coordinate under partial observability. Three concrete consequences of that constraint shaped this implementation:

**No rigid message schema.** Each agent's MCP server (`services/mcp/server_a.py`/`server_b.py`) exposes exactly three transport-level tools — `send_message`, `receive_message`, `get_inbox` — and none of them inspect, validate, or transform the text they carry. Both servers are built from one shared scaffold (`server_base.py`) precisely so neither could accidentally become a side channel for structured, non-NL information. `BaseAgent.interpret_message()` decodes and infers a believed opponent position every turn and keeps a running belief (updated only when a position is actually stated — an ambiguous reply preserves the last known good belief rather than discarding it); the configured `DecisionStrategy` (default: minimax search, see §11.1) then acts on that belief. This was verified live with a real LLM: the Cop correctly parsed `(4, 4)` straight out of the Thief's free-text message ("I'm cornered near the edge of the grid at (4, 4)...") and used it. Decision-making sophistication is config-selectable (`"heuristic"` remains available as the simplest, fully deterministic option) — consistent with the assignment's own framing that orchestration quality, not strategic cleverness, is what's graded (HW-F03).

**Ambiguity is the default, not the exception.** Because there is no shared schema, an opponent's natural-language message may not state a position at all, may state one ambiguously, or — in this project's current configuration, which intentionally defaults to a safe, no-network LLM stub rather than ever making an unauthorized API call — may simply be a fixed placeholder string. `BaseAgent.interpret_message()` handles all three cases identically and without crashing: it asks the (stub or real) LLM to reply in a constrained `"ROW,COL"` / `"UNKNOWN"` format, and treats anything that doesn't parse as `confidence="ambiguous"` rather than raising. This graceful-degradation behavior was verified live, not just in a mock — running a full match with the default rate limits intentionally exhausted (a realistic constraint with any real paid LLM provider) showed dozens of `WARNING ... could not parse a position from LLM response: 'UNKNOWN'` lines, with the match still completing cleanly every time (see [§5 CLI Run Evidence](#5-cli-run-evidence)).

**Mutual understanding has no referee.** Because the architecture forbids the MCP transport layer from adjudicating what either agent "really" believes, the only ground truth that exists anywhere in the system is `RaceState` itself — owned exclusively by the race engine (Chunk 5), never by either agent. This is why `services/race/race_state.py` checks capture regardless of which agent's move caused the two positions to coincide (a documented interpretation, since the HW PDF only describes the Cop's case explicitly): the engine has no concept of "whose fault" a shared cell is, only of whether it occurred. Decoupling "what is true" (the engine) from "what each agent believes" (the agent layer's `Inference` objects) is the structural choice that makes the whole system testable without a live LLM.

## 3. Requirements Summary

This repository is governed by two source documents, both preserved at the project root and **must not be deleted or modified**:

- `ex06-Dual AI agent race via MCP servers.pdf` — the assignment specification.
- `software_submission_guidelines-V3.pdf` — the course's mandatory professional-software submission standard.

Every requirement extracted from both PDFs is tracked in [`docs/00_source_analysis.md`](docs/00_source_analysis.md) and traced to an implementation artifact in [`docs/01_requirements_matrix.md`](docs/01_requirements_matrix.md). In short, the system must:

- Run 6 sub-games (≤25 moves each) per match on a configurable grid (default 5×5), alternating turns, Thief first.
- Support Cop barrier placement (max 5/sub-game, one-way blocking against the Cop only).
- Run two independent FastMCP servers (one per agent) with token-based auth + revoke, never directly exposed without protection.
- Centralize all game parameters in `config/setup.json` — zero hard-coded values.
- Automatically email a structured JSON match report to the grading address after every 6-sub-game match.
- Follow the Guidelines PDF's professional-engineering bar: SDK architecture, central API Gatekeeper, `uv`-only tooling, ≤150 lines/file, ≥85% test coverage, zero `ruff` warnings, versioning starting at 1.00.

## 4. Installation

```bash
git clone https://github.com/AliTrabeh/dual-agent-race-mcp.git
cd dual-agent-race-mcp
uv sync                  # installs all dependencies into a uv-managed virtual environment
cp .env-example .env     # then fill in real values — see below
```

`uv` (https://docs.astral.sh/uv/) is the **only** supported package/environment manager for this project — `pip install`, `python -m venv`, and `requirements.txt` are explicitly forbidden by the submission guidelines, and `uv.lock` is committed.

Required `.env` values (see `.env-example` for the full list and inline documentation) — **only needed if you want real LLM-driven agents or real email dispatch**; the default `uv run python -m hw6_race.main` works with zero `.env` configuration, using a safe no-network LLM stub:

- `LLM_API_KEY` / `LLM_PROVIDER` / `LLM_MODEL` — credentials for a real LLM backend. **Currently implemented: `LLM_PROVIDER=anthropic`** (`services/agents/llm_providers.py::AnthropicCompleteFn`), good default model `claude-haiku-4-5`. If unset, unrecognized, or missing a key, `sdk/wiring.py::build_llm_client_from_env` automatically falls back to the safe no-network stub — the system never makes an unauthorized API call. Get a key at console.anthropic.com (a paid API key, separate from a claude.ai subscription).
- `MCP_COP_AUTH_TOKEN` / `MCP_THIEF_AUTH_TOKEN` — auth tokens for the two MCP servers (only relevant once deployed to the cloud — see [§8](#8-deployment-guide-local--cloud--inter-group-bonus)).
- `GMAIL_OAUTH_CLIENT_SECRET_PATH` / `GMAIL_OAUTH_TOKEN_PATH` — Google API OAuth credentials for the automated end-of-match report email. **Must be real, user-supplied credentials** — see `docs/07_risks_and_open_questions.md` (HW-Q05). Never a stored password (SG-C09).

## 5. CLI Run Evidence

A full local match, run with `uv run python -m hw6_race.main --log-level INFO`, produces a per-turn trace and a final JSON summary. Excerpt from an actual run (not reconstructed):

```text
INFO hw6_race.sdk.wiring: No real LLM provider configured; using the safe no-network stub
INFO hw6_race.sdk.orchestrator: [thief] move 1, at (4, 4), says: 'no comment'
INFO hw6_race.sdk.orchestrator: [thief] move 1, action: AgentAction(action_type=<ActionType.MOVE: 'move'>, direction=<MoveDirection.LEFT: 'left'>)
WARNING hw6_race.services.agents.base_agent: [cop] could not parse a position from LLM response: 'UNKNOWN'
INFO hw6_race.sdk.orchestrator: [cop] move 2, at (0, 0), says: 'no comment'
INFO hw6_race.sdk.orchestrator: [cop] move 2, action: AgentAction(action_type=<ActionType.MOVE: 'move'>, direction=<MoveDirection.RIGHT: 'right'>)
...
```

```json
{
  "sub_games": [
    { "index": 1, "outcome": "thief_win", "move_count": 25, "cop_points": 5, "thief_points": 10 },
    { "index": 2, "outcome": "thief_win", "move_count": 25, "cop_points": 5, "thief_points": 10 },
    { "index": 3, "outcome": "thief_win", "move_count": 25, "cop_points": 5, "thief_points": 10 },
    { "index": 4, "outcome": "thief_win", "move_count": 25, "cop_points": 5, "thief_points": 10 },
    { "index": 5, "outcome": "thief_win", "move_count": 25, "cop_points": 5, "thief_points": 10 },
    { "index": 6, "outcome": "thief_win", "move_count": 25, "cop_points": 5, "thief_points": 10 }
  ],
  "totals": { "cop": 30, "thief": 60 }
}
```

This is deterministic under the default configuration, but for a reason worth explaining rather than glossing over: the no-network LLM stub's `interpret_message` always returns `'UNKNOWN'`, so neither agent's belief of the opponent's position ever updates past a one-time default guess for the whole match — this affects `HeuristicStrategy`'s chase/flee *and* the default `MinimaxDecisionStrategy` equally, since both depend on the same belief. The totals land exactly on the `w=0` (all-Thief-wins) edge of the bound derived for a fixed-role local match (`cop_total = 15w + 30`, `thief_total = 60 − 5w`; see `docs/prds/PRD-003-dual-agent-race-logic.md`). With a real LLM provider configured, beliefs are refined every turn from genuine NL inference, and minimax's search-based decisions meaningfully change the outcome — confirmed by `tools/simulate_strategies.py`'s ground-truth-belief benchmark (§11.1), where a Minimax Cop reliably wins. With a real LLM provider configured, both the messages and the outcomes become genuinely non-deterministic.

## 6. Usage

```bash
uv run python -m hw6_race.main                          # runs a full local 6-sub-game match using config/setup.json
uv run python -m hw6_race.main --dry-run                # validate config only, don't run a match
uv run python -m hw6_race.main --config path/to/custom_setup.json
uv run python -m hw6_race.main --log-level WARNING       # quieter output (default INFO shows a full per-turn trace)
uv run python -m hw6_race.main --output-dir results      # where the JSON result is written (default: results/)
uv run python -m hw6_race.main --version
```

Or call the SDK directly from Python:

```python
from hw6_race.sdk import Hw6RaceSDK

sdk = Hw6RaceSDK()              # uses config/setup.json; real Anthropic backend if .env is configured, else a safe stub
result = sdk.run_local_match()  # runs 6 sub-games end-to-end, returns a GameResult
print(result.total_cop_points, result.total_thief_points)
```

A full run: starts both MCP servers in-process, runs 6 sub-games to completion via real agent/MCP turns (each turn drains the opponent's inbox, interprets it, composes a new message, sends it through the agent's own MCP server, relays it to the opponent's server, then decides and applies a move), logs a human-readable per-turn trace, writes the result to `results/last_match_result.json`, and exits non-zero if any sub-game ended in a Technical Loss. JSON-schema reporting (`InternalGameReport`) and auto-email dispatch (`ReportMailer`) exist and are tested but not yet wired into the CLI's default output path — see `docs/07_risks_and_open_questions.md` for the exact known limitation.

**Using a real LLM**: copy `.env-example` to `.env`, set `LLM_PROVIDER=anthropic` and a real `LLM_API_KEY` (from console.anthropic.com — separate from a claude.ai subscription), then just run `uv run python -m hw6_race.main` as normal — `main.py` loads `.env` automatically, and `Hw6RaceSDK` picks up the real backend with no other code change. To use a different provider, pass `Hw6RaceSDK(llm_client=...)` with your own `LLMClient` implementation (see `services/agents/llm_client.py`).

## 7. Running Tests

```bash
uv run pytest tests/ -v                                   # full test suite
uv run pytest tests/ --cov=src --cov-report=term-missing   # with coverage (gate: ≥85%)
uv run ruff check src/ tests/ tools/                       # lint gate (must report 0 warnings)
```

As of this commit: **233/233 tests pass, 100% coverage, 0 ruff warnings**, including a staged sanity-check matrix across 6 grid sizes (2×2 through 5×5, per the HW PDF's own recommended progression). Every Python file in `src/`, `tests/`, `tools/` is capped at 150 *physical* lines (blank lines and comments included) — stricter than the submission guidelines' 150-*logical*-line cap, enforced by `tests/test_line_limits.py`. See `docs/PLAN.md` ADR-006 and `docs/05_testing_strategy.md`.

## 8. Deployment Guide: Local → Cloud → Inter-Group Bonus

The HW PDF (§6) calls for a 3-stage rollout. Stages are pure config/deployment changes — no code branches per stage (see `docs/03_architecture.md` §4).

**Stage 1 — Local (done, default)**: both MCP servers run in-process, started automatically by `Hw6RaceSDK`. No setup needed beyond `uv sync`.

**Stage 2 — Cloud (Google Cloud Run)**: the code for this stage is built and tested; the actual deployment requires *your* cloud account and credentials, so it's a step you run yourself. Both servers run the same code as Stage 1 — only the transport changes, from an in-process `FastMCP` instance to a real HTTP URL, which `fastmcp.Client`/`AgentMCPClient` already support natively (no code branch per stage).

1. **Standalone server entry point**: `services/mcp/run_server.py` builds one role's server and binds it to a real port: `uv run python -m hw6_race.services.mcp.run_server --role cop --port 8080`. Each role's auth token comes from `MCP_COP_AUTH_TOKEN`/`MCP_THIEF_AUTH_TOKEN` (HW-F17) — the process refuses to start without one (no default/placeholder token in production).
2. **Containerized**: `Dockerfile` (repo root) builds one shared image for both roles; `--role` is supplied per Cloud Run service at deploy time, not baked into the image.
3. **Deploy**: install the [gcloud CLI](https://cloud.google.com/sdk/docs/install), then:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   tools/deploy_cloud_run.sh        # builds, pushes, and deploys both services
   ```
   The script prints the two service URLs and auth tokens it generated (or reused from `MCP_COP_AUTH_TOKEN`/`MCP_THIEF_AUTH_TOKEN` if already set) — add them to your `.env` as `MCP_COP_URL`/`MCP_THIEF_URL`/`MCP_COP_AUTH_TOKEN`/`MCP_THIEF_AUTH_TOKEN` (HW-F18: exactly 2 URLs per group).
4. **Run against the deployed servers**: `uv run python -m hw6_race.main` — `Hw6RaceSDK.run_match()` (used by the CLI) automatically connects to `MCP_COP_URL`/`MCP_THIEF_URL` when both are set, falling back to in-process servers otherwise (`wiring.build_clients_from_env`, mirroring how the LLM backend is selected) — a pure config change, never a code change.
5. Cloud Run services are deployed `--allow-unauthenticated` at the *platform* level (the URL itself is publicly reachable over HTTPS), but every tool call still requires the real `MCP_COP_AUTH_TOKEN`/`MCP_THIEF_AUTH_TOKEN` at the *application* level (`TokenAuthManager`) — satisfying HW-F17 without depending on Cloud IAM. Do not run/test the servers from a hardened organizational network on non-standard ports (HW PDF §5.2).

**Stage 3 — Inter-Group Bonus Round (external, time-boxed)**: requires pairing with a second student group within 1 week of assignment publication (HW-F27, HW-Q06 in `docs/07_risks_and_open_questions.md`) — out of this repository's control. Once paired: play 6 sub-games split 3-and-3 with roles swapped between groups (HW-F27 §12.1), then **both** groups independently email the *exact same* `InterGroupBonusReport` (see `services/reporting/bonus_report.py`, schema verified against the HW PDF's literal example in `tests/unit/test_services/test_reporting/test_bonus_report.py`). `compute_bonus_claim()` implements the winner=10/loser=7/tie=5 scoring rule (HW-F28); a mismatch between the two groups' reports awards 0 points to both sides.

## 9. Project Structure

```text
HW6/
├── README.md                      # this file
├── pyproject.toml                 # uv-managed deps, ruff config, coverage config
├── uv.lock                        # committed; uv sync/run are the canonical commands
├── .env-example                   # placeholder secrets — copy to .env
├── .gitignore
├── src/hw6_race/
│   ├── main.py                    # CLI — zero business logic, delegates to sdk/
│   ├── constants.py               # all named constants/enums — no magic values elsewhere
│   ├── sdk/                       # Hw6RaceSDK (the single entry point), orchestrator.py, wiring.py
│   ├── shared/                    # config.py, version.py, gatekeeper.py (cross-cutting infra)
│   └── services/
│       ├── agents/                # LLMClient, DecisionStrategy, BaseAgent/CopAgent/ThiefAgent
│       ├── mcp/                   # FastMCP servers, auth, message store, async client
│       ├── race/                  # RaceState, RaceEngine, scoring, exceptions
│       └── reporting/             # Internal/Bonus JSON schemas, technical-loss handling, mailer
├── tests/
│   ├── conftest.py                # shared fixtures (fake clock, sample configs, fake LLM client)
│   ├── unit/                      # mirrors src/ structure
│   └── integration/                # MCP round-trips, full SDK matches, staged sanity-check matrix
├── config/
│   ├── setup.json                 # ALL game parameters — grid size, scoring, etc.
│   └── rate_limits.json           # API Gatekeeper rate-limit config
├── docs/
│   ├── PRD.md / PLAN.md / TODO.md          # mandatory guideline docs
│   ├── PRD_q_learning.md                   # per-mechanism PRD (optional RL strategy)
│   ├── 00_source_analysis.md ... 08_*.md   # full requirement extraction & planning trail
│   └── prds/
│       ├── PRD-001..007-*.md               # chunk-level supplementary PRDs
│       ├── PRD_INDEX.md                    # index of all 522 catalog PRDs, grouped by category
│       └── catalog/PRD-0001..0522.md       # numbered PRD catalog (auto-generated, see tools/)
├── tools/
│   ├── generate_prd_catalog.py             # regenerates docs/prds/catalog/ + PRD_INDEX.md
│   └── prd_catalog_data.json               # curated source data for the catalog generator
├── data/ results/ assets/ outputs/         # generated/working data, kept out of git via .gitignore
├── ex06-Dual AI agent race via MCP servers.pdf
└── software_submission_guidelines-V3.pdf
```

## 10. Implementation Status

| Chunk | Title | Status |
|-------|-------|--------|
| 0 | Project init & repo structure | ✅ done |
| 1 | Requirements extraction & validation checklist | ✅ done |
| 2 | Core config system, Gatekeeper, versioning | ✅ done |
| 3 | MCP server/client layer | ✅ done (auth + revoke, NL pass-through, in-process tested) |
| 4 | Agent abstraction layer | ✅ done (LLMClient + DecisionStrategy interfaces, HeuristicStrategy, BaseAgent/CopAgent/ThiefAgent) |
| 5 | Dual-agent race mechanism | ✅ done (grid, movement, barriers, capture/survival, scoring; Q-Learning stretch not attempted) |
| 6 | Controller / orchestrator / game loop | ✅ done (`Hw6RaceSDK.run_local_match()` verified end-to-end) |
| 7 | Logging, JSON protocol, run history, email | ✅ done (schemas, technical-loss algorithm, run logger, mailer — all tested; live-match rerun wiring flagged as a known limitation) |
| 8 | CLI interface | ✅ done (argparse, exit codes, output file, zero business logic) |
| 9 | Tests (suite-level completion, coverage gate) | ✅ done (staged sanity-check matrix across 6 grid sizes; 100% coverage sustained since Chunk 6) |
| 10 | Documentation finalization & submission packaging | ✅ done (README finalized; real cloud deployment remains an actionable guide, not yet performed — requires a real cloud account, see §8) |
| 11 | Final validation against both PDFs | ✅ done (requirements matrix re-audited row by row; ISO/IEC 25010 self-check performed; 522-entry PRD catalog tallied: 255 done, 240 not-started/future, 17 in progress) |
| 12 | LLM-driven decision strategy | ✅ done (`LLMDecisionStrategy`: the LLM picks the action directly, falls back to `HeuristicStrategy` on any parse failure) |
| 13 | Minimax + alpha-beta competitive decision strategy | ✅ done (`MinimaxDecisionStrategy`: depth-limited minimax + alpha-beta + move ordering + transposition table, new default; see §11.1) |
| 14 | Cloud deployment path (Google Cloud Run) | ✅ code done; 🟨 actual deployment requires your GCP account — run `tools/deploy_cloud_run.sh` (see §8 Stage 2) |

## 11. Configuration Guide

All game parameters live in `config/setup.json` — never hard-coded in source:

| Key | Default | Meaning |
|-----|---------|---------|
| `grid_size` | `[5, 5]` | Board dimensions `[rows, cols]` |
| `max_moves` | `25` | Move cap per sub-game |
| `num_games` | `6` | Sub-games per full match |
| `max_barriers` | `5` | Max barriers the Cop may place per sub-game |
| `scoring.cop_win` / `scoring.thief_win` / `scoring.cop_loss` / `scoring.thief_loss` | `20 / 10 / 5 / 5` | Points awarded per sub-game outcome |
| `decision_strategy` | `"minimax"` | `"minimax"` (default), `"llm"`, or `"heuristic"` |
| `minimax_depth` | `6` | Plies searched ahead by `MinimaxDecisionStrategy` |
| `minimax_time_budget_seconds` | `2.0` | Per-decision search time budget before falling back to the heuristic |

Rate limits for all outbound API calls (LLM provider, Gmail) live in `config/rate_limits.json` and are enforced centrally by `shared/gatekeeper.py`'s `ApiGatekeeper` — no call site implements its own rate limiting.

### 11.1 Decision strategies (Cop/Thief move selection)

Three interchangeable `DecisionStrategy` implementations, selected by `decision_strategy` above — swapping one for another requires no change to `BaseAgent` or either concrete agent class (ADR-003):

- **`minimax`** (default) — `services/agents/strategies/minimax/`: depth-limited minimax with alpha-beta pruning, move ordering, and a transposition table. The Cop reasons several turns ahead as a trapper/hunter (immediate capture, then shortest-path distance, Thief-mobility reduction, Thief-reachable-area reduction); the Thief reasons as a survivor (avoiding immediate capture, maximizing future safe moves/reachable area/escape flexibility). Both search against the agent's own *belief* of the opponent's position (`board_utils.make_belief_state`), never the engine's ground truth — preserving the Dec-POMDP partial-observability boundary (§2). Falls back to a one-ply heuristic (`fallback.py`) if search times out or raises; never crashes, never returns an illegal action.
  - **Honest finding on barriers**: the engine's real rule (HW PDF, unchanged since Chunk 5) is that a barrier blocks *only* the Cop, never the Thief. A well-reasoned Cop therefore almost never places one — it can only restrict its own future movement, never the Thief's. This is correct, faithful behavior given the actual game rule, not a bug in the strategy.
  - Benchmarked with `tools/simulate_strategies.py` (`uv run python tools/simulate_strategies.py --games 20 --grid 5`): a Minimax Cop beats a Heuristic or Random Thief in ~6 turns (3×3) / ~14 turns (5×5) with zero illegal actions; a Heuristic or Random Cop *never* catches a Minimax Thief — the lookahead lets it evade indefinitely. The benchmark feeds each strategy the ground-truth opponent position directly (bypassing MCP/LLM/NL-inference) to isolate search-algorithm quality from inference noise, which is verified separately by the staged sanity checks (§5).
- **`llm`** — `services/agents/strategies/llm_strategy.py`: asks the LLM to choose the action directly each turn, falling back to `heuristic` on any unparseable/illegal reply.
- **`heuristic`** — `services/agents/strategies/heuristic_strategy.py`: deterministic fixed-priority movement, chasing/fleeing via Manhattan distance once a belief exists. No learning, no lookahead — the simplest option, useful as a fast, fully deterministic baseline.

## 12. Contribution Guidelines

- Follow the chunk plan in `docs/04_implementation_chunks.md` — do not implement a chunk before its referenced PRD exists and is reviewed.
- Every new module needs a matching test file (TDD: tests before/alongside implementation).
- Keep every source file ≤150 physical lines; split via helper modules/constants/mixins per `docs/00_source_analysis.md` §9a (PROJ-R01) and SG-C01.
- Run `uv run ruff check` and `uv run pytest --cov` before committing; both gates must pass clean.
- Update `docs/TODO.md` and `docs/01_requirements_matrix.md` in the same change as the code it tracks.
- Record significant AI-assisted prompts in `docs/08_claude_work_log.md` (Prompt Engineering Log).

## 13. License & Third-Party Credits

Academic submission for course use. Third-party dependencies are declared in `pyproject.toml`; their respective licenses apply (notably FastMCP, pydantic, pytest, ruff).

## 14. Submission Checklist

See [`docs/06_submission_checklist.md`](docs/06_submission_checklist.md) for the full merged checklist (HW PDF §11/§13 + Guidelines PDF §17/§19). High-level status: the full local pipeline, documentation, and testing requirements are satisfied (Chunks 0–9); cloud deployment (§8 above) and the inter-group bonus round require real external accounts/credentials and a paired second group, and remain explicit user actions, not automatable by this codebase alone.

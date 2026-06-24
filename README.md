# HW6 — Dual AI Agent Race via MCP Servers (Cop/Thief Pursuit Game)

**Course**: AI Agents / AI Orchestra — Assignment 6 ("Dual AI Agent Conversation via MCP Servers")
**Status**: Phase 0/1 complete (planning + skeleton). Game logic implementation has **not** started yet — see [Implementation Status](#implementation-status).

## 1. Overview

This project implements a fully autonomous, two-agent pursuit game — a **Cop** and a **Thief**, each backed by its own LLM and its own [MCP](https://modelcontextprotocol.io/) (Model Context Protocol) server — that play a sequence of pursuit episodes on a configurable 2D grid. The two agents never share memory or a rigid message schema: they communicate exclusively through free natural-language text, exchanged via MCP tool calls. Grading for this assignment is explicitly about the quality of that orchestration and communication, **not** about which agent wins more often.

Formally, this is a 2-agent, partially-observable, decentralized pursuit problem — a **Dec-POMDP**:

```
⟨ n, S, {Aᵢ}, P, R, {Ωᵢ}, O, γ ⟩
```

| Symbol | Meaning in this project |
|--------|---------------------------|
| `n = 2` | Cop and Thief agents |
| `S` | Full grid state: Cop position, Thief position, set of up to 5 barriers, move counter |
| `{Aᵢ}` | Thief: 4 movement directions. Cop: 4 movement directions + place-barrier |
| `P` | Deterministic grid transition given a legal action |
| `R` | The fixed scoring table (Cop win → 20/5, Thief win → 10/5), sourced from `config/setup.json` |
| `{Ωᵢ}` | Each agent observes only its own position plus whatever natural-language text the opponent chose to send — this is the partial-observability layer |
| `O` | Implicit in what each agent's MCP server tool returns to its own LLM client — never a shared ground-truth channel |
| `γ` | Discount factor, meaningful only if the optional Q-Learning strategy (`docs/PRD_q_learning.md`) is enabled |

The hardest engineering problem this project targets — named explicitly in the source assignment — is that the two agents are **independent, decoupled, and use free natural language with no shared protocol** to coordinate under partial observability. See `docs/03_architecture.md` for the full discussion of how the architecture isolates this concern from the (separately swappable) decision-making strategy.

## 2. Requirements Summary

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

## 3. Installation

> **Prerequisite**: [`uv`](https://docs.astral.sh/uv/) is the **only** supported package/environment manager for this project — `pip install`, `python -m venv`, and `requirements.txt` are explicitly forbidden by the submission guidelines. Install `uv` first if you don't have it.

```bash
git clone <this-repo-url>
cd HW6
uv sync                  # installs all dependencies into a uv-managed virtual environment
cp .env-example .env     # then fill in real values — see below
```

Required `.env` values (see `.env-example` for the full list and inline documentation):

- `LLM_API_KEY` / `LLM_PROVIDER` / `LLM_MODEL` — credentials for whichever of the 3 supported LLM-connectivity architectures you choose (public cloud API key, local Ollama + tunnel, or the hybrid local-Ollama/cloud-MCP-server setup — see `docs/03_architecture.md` §3).
- `MCP_COP_AUTH_TOKEN` / `MCP_THIEF_AUTH_TOKEN` — auth tokens for the two MCP servers.
- `GMAIL_OAUTH_CLIENT_SECRET_PATH` / `GMAIL_OAUTH_TOKEN_PATH` — Google API OAuth credentials for the automated end-of-match report email. **Must be real, user-supplied credentials** — see `docs/07_risks_and_open_questions.md` (HW-Q05).

## 4. Usage

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

sdk = Hw6RaceSDK()              # uses config/setup.json + a safe no-network LLM stub by default
result = sdk.run_local_match()  # runs 6 sub-games end-to-end, returns a GameResult
print(result.total_cop_points, result.total_thief_points)
```

A full run: starts both MCP servers in-process, runs 6 sub-games to completion via real agent/MCP turns (each turn drains the opponent's inbox, interprets it, composes a new message, sends it through the agent's own MCP server, relays it to the opponent's server, then decides and applies a move), logs a human-readable per-turn trace, writes the result to `results/last_match_result.json`, and exits non-zero if any sub-game ended in a Technical Loss. JSON-schema reporting (`InternalGameReport`) and auto-email dispatch (`ReportMailer`) exist and are tested but not yet wired into the CLI's default output path — see `docs/07_risks_and_open_questions.md` for the exact known limitation. To use a real LLM provider instead of the safe default stub, pass `Hw6RaceSDK(llm_client=...)` with your own `LLMClient` implementation — see `.env-example` for the credential layout.

## 5. Running Tests

```bash
uv run pytest tests/ -v                                   # full test suite
uv run pytest tests/ --cov=src --cov-report=term-missing   # with coverage (gate: ≥85%)
uv run ruff check src/ tests/                              # lint gate (must report 0 warnings)
```

As of this commit: **217/217 tests pass, 100% coverage, 0 ruff warnings**, including a staged sanity-check matrix across 6 grid sizes (2×2 through 5×5, per the HW PDF's own recommended progression). A full local match (`Hw6RaceSDK().run_local_match()`) now runs genuinely end-to-end and is runnable directly from the CLI (`uv run python -m hw6_race.main`), and its `GameResult` can be turned into a submission-schema-exact Internal Game JSON report and emailed (with a mocked send function in tests; real Gmail OAuth credentials are user-supplied, never fabricated) (config loader, version tracking, API Gatekeeper, import-safety checks, and the project-wide 150-line file check). Game logic is not yet present, so these numbers will shift as chunks 3–9 land — see `docs/05_testing_strategy.md`.

**Project rule**: every Python file in this repo (`src/`, `tests/`, `tools/`) is capped at 150 *physical* lines (blank lines and comments included) — stricter than the submission guidelines' 150-*logical*-line cap. Enforced by `tests/test_line_limits.py`, run as part of the normal test suite. See `docs/PLAN.md` ADR-006.

## 6. Project Structure

```text
HW6/
├── README.md                      # this file
├── pyproject.toml                 # uv-managed deps, ruff config, coverage config
├── uv.lock                        # generated by `uv lock` once uv is installed
├── .env-example                   # placeholder secrets — copy to .env
├── .gitignore
├── src/hw6_race/
│   ├── main.py                    # CLI — zero business logic, delegates to sdk/
│   ├── constants.py               # all named constants/enums — no magic values elsewhere
│   ├── sdk/sdk.py                 # SINGLE entry point for all business logic
│   ├── shared/                    # config.py, version.py, gatekeeper.py (cross-cutting infra)
│   └── services/                  # agents/, mcp/, race/, reporting/ (domain logic, built per chunk)
├── tests/
│   ├── conftest.py                # shared fixtures (fake clock, sample configs)
│   ├── unit/                      # mirrors src/ structure
│   └── integration/
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

## 7. Implementation Status

This repository is currently at the end of **Phase 0/1**: full requirement extraction, documentation, and an import-safe skeleton — **no game logic has been implemented yet**, by design (the submission guidelines explicitly forbid writing code before architecture/requirements docs are approved). See `docs/TODO.md` for the live task tracker.

| Chunk | Title | Status |
|-------|-------|--------|
| 0 | Project init & repo structure | ✅ done |
| 1 | Requirements extraction & validation checklist | ✅ done |
| 2 | Core config system, Gatekeeper, versioning | ✅ done (skeleton-level: config loader, version, Gatekeeper implemented + tested) |
| 3 | MCP server/client layer | ✅ done (auth + revoke, NL pass-through, in-process tested) |
| 4 | Agent abstraction layer | ✅ done (LLMClient + DecisionStrategy interfaces, HeuristicStrategy, BaseAgent/CopAgent/ThiefAgent) |
| 5 | Dual-agent race mechanism | ✅ done (grid, movement, barriers, capture/survival, scoring; Q-Learning stretch not attempted) |
| 6 | Controller / orchestrator / game loop | ✅ done (`Hw6RaceSDK.run_local_match()` verified end-to-end; Technical Loss containment in place, full rerun-to-6 is Chunk 7) |
| 7 | Logging, JSON protocol, run history, email | ✅ done (schemas, technical-loss algorithm, run logger, mailer — all tested; live-match rerun wiring flagged as a known limitation) |
| 8 | CLI interface | ✅ done (argparse, exit codes, output file, zero business logic) |
| 9 | Tests (suite-level completion, coverage gate) | ✅ done (staged sanity-check matrix across 6 grid sizes; 100% coverage sustained since Chunk 6) |
| 10 | Documentation finalization & submission packaging | 🟨 this README is a living document, finalized in chunk 10 |
| 11 | Final validation against both PDFs | ⬜ not started |

## 8. Configuration Guide

All game parameters live in `config/setup.json` — never hard-coded in source:

| Key | Default | Meaning |
|-----|---------|---------|
| `grid_size` | `[5, 5]` | Board dimensions `[rows, cols]` |
| `max_moves` | `25` | Move cap per sub-game |
| `num_games` | `6` | Sub-games per full match |
| `max_barriers` | `5` | Max barriers the Cop may place per sub-game |
| `scoring.cop_win` / `scoring.thief_win` / `scoring.cop_loss` / `scoring.thief_loss` | `20 / 10 / 5 / 5` | Points awarded per sub-game outcome |
| `decision_strategy` | `"heuristic"` | `"heuristic"` or `"q_learning"` (see `docs/PRD_q_learning.md`) |

Rate limits for all outbound API calls (LLM provider, Gmail) live in `config/rate_limits.json` and are enforced centrally by `shared/gatekeeper.py`'s `ApiGatekeeper` — no call site implements its own rate limiting.

## 9. Contribution Guidelines

- Follow the chunk plan in `docs/04_implementation_chunks.md` — do not implement a chunk before its referenced PRD exists and is reviewed.
- Every new module needs a matching test file (TDD: tests before/alongside implementation).
- Keep every source file ≤150 logical lines; split via helper modules/constants/mixins per `docs/00_source_analysis.md` SG-C01.
- Run `uv run ruff check` and `uv run pytest --cov` before committing; both gates must pass clean.
- Update `docs/TODO.md` and `docs/01_requirements_matrix.md` in the same change as the code it tracks.
- Record significant AI-assisted prompts in `docs/08_claude_work_log.md` (Prompt Engineering Log).

## 10. License & Third-Party Credits

Academic submission for course use. Third-party dependencies are declared in `pyproject.toml`; their respective licenses apply (notably FastMCP, pydantic, pytest, ruff).

## 11. Submission Checklist

See [`docs/06_submission_checklist.md`](docs/06_submission_checklist.md) for the full merged checklist (HW PDF §11/§13 + Guidelines PDF §17/§19). High-level status: documentation and skeleton requirements are satisfied; game logic, MCP servers, cloud deployment, and the automated email report are pending chunks 3–10.

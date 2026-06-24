# PRD — HW6: Dual AI Agent Race via MCP Servers

> Mandatory per Guidelines PDF SG-D02. This is the single canonical product requirements document for the whole project. Per-mechanism PRDs live in `docs/PRD_<mechanism>.md` (SG-D03) and chunk-level PRDs live in `docs/prds/` (supplementary, user-requested).

## 1. Overview & Context

This project implements course assignment "Dual AI Agent Conversation via MCP Servers" (HW6, AI Orchestra course). Two independent, fully autonomous AI agents — **Cop** and **Thief** — play a pursuit game on a configurable 2D grid. Each agent is backed by its own MCP (Model Context Protocol) server built with FastMCP, and the two agents communicate **only** via free natural-language text messages exchanged through their respective MCP tool interfaces — never through shared memory or a rigid message schema. See `docs/00_source_analysis.md` HW-F01–F03.

## 2. Problem Statement

Multi-agent systems in the real world coordinate (or compete) under partial observability and without a shared, hard-coded protocol. This project is a teaching vehicle for that problem: build a working pipeline that proves two LLM-backed agents can use natural language, exchanged over MCP tool calls, to play a Dec-POMDP-style pursuit game to completion — repeatedly, autonomously, and measurably.

## 3. Target "User" / Audience

The primary audience is the course grader, who will: (a) read the GitHub repo + README as a scientific write-up, (b) run the local pipeline end-to-end, (c) optionally inspect cloud-deployed MCP servers and an inter-group bonus game JSON exchange. Secondary "users" are the two AI agents themselves, who are MCP clients/tool consumers of each other's servers.

## 4. Goals, KPIs, Acceptance Criteria

| Goal | KPI | Acceptance criteria |
|------|-----|----------------------|
| Working local pipeline | 6/6 sub-games complete without unhandled exceptions | A full `uv run python -m hw6_race.main` run produces a complete Internal Game JSON with `totals.cop + totals.thief` consistent with the scoring table |
| Orchestration quality | Both agents converge to a shared understanding without a rigid protocol | Logs show each Cop/Thief turn includes a free-text NL message plus a derived legal move |
| Config-driven behavior | 0 hard-coded game parameters | `grep` for magic numbers in `src/` related to grid size/moves/scoring returns none outside `constants.py`/config |
| Submission compliance | Passes the Guidelines PDF quick-reference gate table (p.33) | `ruff check` 0 warnings, `pytest --cov` ≥85%, all files ≤150 lines, docs present |
| Reporting compliance | Auto-generated JSON matches schema exactly | JSON validated against the schema in `docs/00_source_analysis.md` HW-F23 before send |

## 5. Functional Requirements

See `docs/01_requirements_matrix.md` rows HW-F01 through HW-F29 — all are in-scope functional requirements for v1 unless flagged optional (Q-Learning, GUI) or external (inter-group bonus play itself).

## 6. Non-Functional Requirements

See `docs/01_requirements_matrix.md` rows HW-N01–N06 and all SG-C/SG-T/SG-U rows — architecture (SDK + Gatekeeper), code quality (150-line cap, no duplication), testing (TDD, 85% coverage), tooling (`uv` only), security (token auth, `.env` secrets), versioning (starts at 1.00).

## 7. User Stories

- As the grader, I want a single command to run a full local 6-sub-game match so I can verify the pipeline works end-to-end.
- As the grader, I want the README to formally define the Dec-POMDP tuple for this game so I can assess theoretical understanding.
- As the Cop agent, I want to send and receive natural-language position hints through my own MCP server so I never need direct access to the Thief's internal state.
- As the Thief agent, I want to automatically email the final JSON report after the 6th sub-game so no manual reporting step is required.
- As a second group in the inter-group bonus round, I want a stable, authenticated MCP URL for the Cop and Thief servers so our agents can play against this group's agents without exposing internals.

## 8. Functional vs. Non-Functional Split & Anti-Requirements

In scope: grid/race engine, MCP server/client layer, pluggable LLM-backed decision strategy (heuristic default, Q-Learning optional), JSON reporting + Gmail dispatch, config system, API Gatekeeper, test suite, docs.

Out of scope / anti-requirements: implementing a GUI is optional and not required for grading; deep-RL (neural Q-function) is explicitly discouraged by the source PDF in favor of tabular Q-Learning; actually playing the inter-group bonus match is an external, manual, time-boxed activity this codebase enables but does not itself perform.

## 9. Constraints, Dependencies, Out-of-Scope

- Constraint: `uv` is the only allowed package manager (SG-U01). No `pip`, no `requirements.txt`.
- Constraint: every file ≤150 logical lines (SG-C01) — forces aggressive modularization of the race engine and MCP layer.
- Dependency: a real LLM provider API key (or local Ollama) supplied by the user via `.env` — cannot be fabricated by the assistant.
- Dependency: real Gmail/Google API OAuth credentials supplied by the user for HW-F21 — cannot be fabricated.
- Out of scope (this repo alone): a second student group to actually run the bonus match against (HW-F27).

## 10. Timeline / Phases

Tracked in `docs/TODO.md` and `docs/04_implementation_chunks.md` — chunks 0–11, following the HW PDF's own recommended 8-stage development order (HW-F29) nested inside the Guidelines PDF's SDLC stage order (SG-P02).

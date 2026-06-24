# PRD-004 — Controller and Orchestration

## Purpose

Build the orchestrator — the MCP **client** role described in the HW PDF — that ties together the race engine (PRD-003), the two MCP servers (PRD-002), and each agent's decision strategy/LLM client (chunk 4) into one runnable game loop. This is the chunk where "two independent agents conducting an autonomous natural-language negotiation about positions" actually becomes an executable program rather than three separate pieces.

## Scope

In scope: `sdk/sdk.py` (the single public entry point — SG-C03), `services/agents/base_agent.py` (shared agent abstraction: holds an `LLMClient`, a `DecisionStrategy`, and MCP client handles), `services/agents/cop_agent.py` / `services/agents/thief_agent.py` (concrete agents, thin subclasses), and the actual per-turn orchestration loop that calls each agent for a natural-language message, calls its MCP tool, derives a legal action, and feeds it to `RaceEngine`.

Out of scope: the race rules themselves (already in PRD-003), MCP transport internals (already in PRD-002), JSON reporting (PRD-005) — this chunk only needs to *produce* the final `GameResult` and hand it off.

## Requirements Covered

HW-F01 (end-to-end pipeline), HW-F02 (decode NL → infer location → translate to move), HW-F15 (LLM lives in the client/orchestrator, never the server), HW-F19 (pluggable LLM connectivity architecture — the orchestrator is where the `LLMClient` interface is actually consumed), HW-N01/N02 (free NL, no rigid protocol, client/server split). SG-C03 (SDK single entry point), SG-C04 (no duplicated logic between Cop/Thief agent classes — shared behavior lives in `base_agent.py`).

## Inputs and Outputs

**Inputs**: configuration (which LLM architecture, which decision strategy, MCP server URLs/ports), the two MCP server instances (or their URLs if already running), the race engine.

**Outputs**: a `GameResult` from a full 6-sub-game run, plus a structured per-turn trace log (each agent's NL message + derived action) used both for debugging and as the HW PDF's required "CLI run evidence" in the README.

## Components / Files Likely Needed

- `sdk/sdk.py` — `Hw6RaceSDK` class: `run_local_match(config) -> GameResult`, the one function CLI/tests are allowed to call for end-to-end behavior.
- `services/agents/base_agent.py` — abstract base: `decide_action(observation) -> Action`, `compose_message(context) -> str`, `interpret_message(text) -> Inference`; holds the `LLMClient` and `DecisionStrategy` collaborators, delegates rather than duplicates their logic.
- `services/agents/cop_agent.py`, `services/agents/thief_agent.py` — role-specific prompt templates and the one or two behavioral differences (Thief moves first, Cop can place barriers) — everything else inherited.
- `services/agents/llm_client.py` — the `LLMClient` interface plus at least one concrete implementation (e.g. a cloud-API-key client), routed through `shared/gatekeeper.py` for every call.

## Acceptance Criteria

- `Hw6RaceSDK.run_local_match()` runs a full match using real (or test-double) MCP servers and produces a complete `GameResult` with no direct cross-talk between Cop/Thief internal state outside of what passed through MCP messages.
- Swapping the configured `DecisionStrategy` (heuristic vs. Q-Learning, per `docs/PRD_q_learning.md`) requires no change to `base_agent.py`, `cop_agent.py`, or `thief_agent.py`.
- Swapping the configured LLM architecture (cloud API / Ollama / hybrid, per HW-F19) requires no change to the race or MCP layers — only `LLMClient` construction changes.
- Every LLM API call made during a match goes through `ApiGatekeeper.execute(...)`, never a direct provider SDK call.

## Edge Cases

- An agent's LLM returns text that doesn't parse into any inferable position/intent — `interpret_message` must return a clearly-typed "ambiguous" result rather than raising, and the calling agent must fall back to a safe default action (e.g., stay/random legal move) — this is the orchestration-robustness property the HW PDF cares most about.
- One agent's MCP call times out or errors mid-sub-game — orchestrator must catch this at the sub-game boundary and mark it eligible for Technical Loss / rerun (handed to PRD-005's reporting logic), not crash the whole 6-sub-game match.
- Both agents converge on contradictory beliefs about position (e.g., both think the Thief is in cell 12 but it's actually in cell 7) — this is expected/valid behavior under partial observability, not a bug; tests should assert the *engine* handles it (engine doesn't care what either agent believes, only what's true), not that agents are always "right."

## Testing Requirements

Unit tests for `base_agent.py`'s message-interpretation fallback behavior using scripted/mocked LLM responses (well-formed, malformed, empty). Integration test running `Hw6RaceSDK.run_local_match()` against the real `RaceEngine` and either real local MCP servers or lightweight in-process doubles, with both agents' `LLMClient`s mocked to return deterministic scripted responses — keeping the test suite fast and CI-safe per SG-T03 ("no test depends on a live external service").

## Risks

This is the most integration-heavy chunk and the most likely place for the project's core "is this actually two independent agents talking, or is it secretly one program cheating" property to be silently violated during implementation under time pressure. Code review should specifically check that no orchestrator code path reads Thief state to help compose the Cop's message, or vice versa — only what arrived via an MCP tool call is fair game.

## Definition of Done

A scripted end-to-end match runs via `Hw6RaceSDK.run_local_match()`, both decision-strategy and LLM-architecture swaps are demonstrated to require zero changes outside their own modules, all files ≤150 lines, and `docs/TODO.md`'s "Chunk 4" and "Chunk 6" rows updated to `done`.

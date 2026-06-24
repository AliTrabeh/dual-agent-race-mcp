# 03 — Architecture (Narrative)

Companion to the structured artifacts in `docs/PLAN.md`. This document carries the deeper discussion the Guidelines PDF expects in architecture documentation, applied specifically to the Dec-POMDP / MCP problem from the HW PDF.

## 1. Why this is a Dec-POMDP, formally

The HW PDF requires the README to state the formal tuple `⟨n, S, {Ai}, P, R, {Ωi}, O, γ⟩` (HW-F26). The architecture must be built so each element of that tuple maps cleanly onto a real module:

- `n = 2` agents — Cop and Thief — implemented as two independent `services/agents` instances, each with its own MCP server.
- `S` (state space) — full grid state: positions of Cop, Thief, and up to 5 barriers on a `grid_size[0] × grid_size[1]` board → `services/race/race_state.py`.
- `{Ai}` (per-agent action spaces) — Thief: 4 movement directions; Cop: 4 movement directions + place-barrier → `services/race/race_engine.py` validates legality per agent.
- `P` (transition function) — deterministic grid update given a legal action → `RaceState.apply_action()`.
- `R` (reward/scoring function) — the fixed scoring table (20/5 cop-win, 10/5 thief-win) → `services/race/scoring.py`, values sourced from `config/setup.json`, never hard-coded (HW-F25).
- `{Ωi}` (per-agent observation spaces) — each agent observes only what its own MCP tool calls receive: its own position, and whatever natural-language hints the opponent chose to send — this is the partial-observability layer (`tzaffit chelkit` in the source PDF).
- `O` (observation function) — modeled implicitly by what each agent's MCP server tool returns to its own LLM client; deliberately *not* a shared ground-truth channel.
- `γ` (discount factor) — only meaningful if the optional Q-Learning strategy is used (`docs/PRD_q_learning.md`); irrelevant to the heuristic strategy.

## 2. Orchestration challenge: free natural language, no rigid protocol

The hardest engineering problem named explicitly in the HW PDF (§14, "Central insights") is that the two agents are independent, decoupled, and use free natural language with **no shared protocol** to coordinate. This has direct architectural consequences:

- The MCP servers must not become a backdoor shared-state channel. `server_a.py`/`server_b.py` only ever pass through whatever text content the calling agent's LLM produced — no server-side cross-referencing of Cop/Thief internal state.
- Ambiguity handling lives in the agent layer (`services/agents`), not the transport layer (`services/mcp`). If an agent's LLM produces a vague or malformed message, the receiving agent's prompt must be designed to degrade gracefully (re-ask, assume a default, etc.) rather than crash the pipeline — this is also a testing requirement (SG-T05, edge cases).
- Because grading rewards orchestration/communication quality over win-rate (HW-F03), the architecture intentionally keeps the decision *strategy* (heuristic vs. Q-Learning) swappable and separate from the *communication* layer, so the latter can be evaluated independently.

## 3. Client/Server separation and the 3 LLM-connectivity architectures

Per HW-F15/HW-F19, the LLM must never live inside the MCP server. The orchestrator (`sdk/sdk.py`) is the MCP **client**: it calls `Tool Call` on each agent's MCP server, and is also the only place an LLM API call happens. This split lets the same MCP server code run unmodified regardless of which of the 3 LLM architectures the user picks:

1. **Public cloud API** (OpenAI/Anthropic/Gemini key) — simplest; `services/agents/base_agent.py` defines an `LLMClient` interface so swapping providers is a config change, not a code change.
2. **Local Ollama + secure tunnel** (ngrok/Localtonet/Nginx) — the MCP server is still local; only the tunnel changes. No code impact, only deployment config.
3. **Hybrid (recommended for secure local dev)** — Ollama stays on loopback, only the MCP server is exposed to the cloud, and all outbound calls from the client are HTTPS-only. This is the safest default we document in the README's deployment section.

The Gatekeeper (`shared/gatekeeper.py`) sits in front of whichever LLM client is configured, so rate limiting/retries/logging are identical regardless of architecture choice.

## 4. Staged rollout and staged sanity checks are the same axis, twice

The HW PDF names two parallel "make it smaller first" mechanisms that the architecture must support simultaneously: (a) grid-size sanity-check stages (2×2 → 3×3 → 4×4 → 5×5, HW-F12) and (b) deployment sanity-check stages (localhost → cloud → bonus competition, HW-F16). Because `grid_size` is a config value (HW-F06) and MCP server URLs are also config values (HW-F18), both axes are exercised purely by changing `config/setup.json` between test runs — no code branching is needed for either axis. This is itself an architecture decision worth stating explicitly: **the sanity-check matrix is a test-fixture concern, not a code-path concern.**

## 5. Security architecture

Token-based auth with revoke (HW-F17) is implemented once, in `services/mcp/server_base.py`, and inherited by both `server_a.py` and `server_b.py` (avoids the duplication SG-C04 forbids). Tokens themselves are read only via `os.environ.get(...)` (SG-C09) — never embedded in `config/setup.json`, since that file is meant to be committed.

## 6. Reporting architecture

The Internal Game JSON and Inter-Group Bonus JSON (HW-F23/F24) are modeled as typed schemas in `services/reporting/schemas.py`, built incrementally by `services/race/race_engine.py` as each sub-game completes, and only serialized/emailed once at the very end of the 6th sub-game (HW-F21). The Gmail dispatch call itself goes through the same `ApiGatekeeper` as LLM calls (ADR-004 in `docs/PLAN.md`), so rate-limit/retry/logging behavior is uniform across both kinds of external calls the system makes.

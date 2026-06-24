# PRD-002 — MCP Server Layer

## Purpose

Build the two independent MCP servers — one for the Cop agent, one for the Thief agent — using FastMCP, satisfying the HW PDF's explicit architectural requirement that the agents never share state directly and communicate only through free natural-language tool calls. This is the transport layer the rest of the system depends on; getting the security and isolation properties right here is what makes the later cloud-deployment and inter-group bonus stages (chunks 10/11) viable without rework.

## Scope

In scope: `services/mcp/server_base.py` (shared FastMCP scaffold: tool registration, token-based auth with revoke, structured logging of all tool calls), `services/mcp/server_a.py` (Cop server: `send_message`, `get_position_hint`, `place_barrier_notice` tools), `services/mcp/server_b.py` (Thief server: `send_message`, `get_position_hint` tools), and the MCP **client**-side calling code that lives in the orchestrator (`sdk/sdk.py`, built out further in chunk 6) — this chunk only needs enough client-side plumbing to test the servers end-to-end.

Out of scope: cloud deployment/tunneling configuration (chunk 10), the actual race rules (chunk 5) — this chunk's tools pass natural-language text through; they do not interpret or validate game legality themselves.

## Requirements Covered

HW-F13 (two independent MCP servers), HW-F14 (FastMCP-based tool exposure), HW-F15 (LLM decoupled from server; client = orchestrator), HW-F17 (token auth + revoke, no unprotected public exposure), HW-F18 (exactly 2 URLs per group). SG-C04 (no duplicated auth/tool-registration logic between `server_a.py` and `server_b.py` — both inherit from `server_base.py`). SG-C12 (I/O-bound network work — async/threading guidance applies here, not multiprocessing).

## Inputs and Outputs

**Inputs**: natural-language text messages produced by each agent's LLM client (chunk 4); a bearer/token credential read from `.env` via `os.environ.get(...)`.

**Outputs**: the same natural-language text, passed through to the receiving MCP client unmodified, plus structured call logs (caller identity, timestamp, tool name) for observability and for the HW PDF's required "CLI run evidence" in the final README.

## Components / Files Likely Needed

- `services/mcp/server_base.py` — auth middleware, tool registration helpers, request logging; ≤150 lines, so any tool-specific logic is deliberately kept in `server_a.py`/`server_b.py`.
- `services/mcp/server_a.py`, `services/mcp/server_b.py` — thin, agent-specific tool definitions only.
- `services/mcp/auth.py` — token issuance/verification/revoke, isolated so it's independently unit-testable (mirrors the Guidelines PDF's mixin-independence rule even though this isn't literally a mixin).
- `services/mcp/client.py` — minimal MCP client wrapper used by the orchestrator to call `Tool Call` against either server.

## Acceptance Criteria

- Both servers can be started independently on separate localhost ports (HW-F16 stage 1) with zero shared in-process state between them.
- A request without a valid token is rejected with a clear 401-equivalent error; a revoked token is rejected immediately, with no caching of stale validity.
- Calling `send_message` on the Cop server and reading it back via the Thief server's `get_position_hint` (or equivalent) round-trips the exact text with no silent transformation — proving the "no rigid protocol, no shared state" property from HW-F13/HW-N01.
- No tool implementation in `server_a.py`/`server_b.py` duplicates the auth-check or logging logic already in `server_base.py`.

## Edge Cases

- Two rapid-fire calls from the same agent before the previous one is processed (concurrency) — must not corrupt the message log or cross-deliver to the wrong recipient.
- Auth token expires mid-sub-game — server must reject gracefully without crashing the orchestrator's overall run; the orchestrator must surface this as a Technical Loss candidate (ties into chunk 7's reporting logic), not an unhandled exception.
- A malformed/oversized message payload — server enforces a reasonable size cap (config-driven, not magic-numbered) rather than passing arbitrary content downstream unchecked.

## Testing Requirements

Unit tests for `server_base.py`'s auth/revoke logic (valid token, invalid token, revoked token, expired token) using FastMCP's test client or an equivalent in-process harness — no real network sockets in unit tests. Unit tests for `services/mcp/auth.py` in isolation. Integration test starting both real servers on ephemeral localhost ports and exercising a full message round-trip, included in `tests/integration/test_mcp_layer.py`. All per SG-T01–T03.

## Risks

FastMCP's exact API surface should be verified against its current documentation when this chunk is implemented (library APIs evolve); this PRD describes the *shape* of the integration (auth middleware + tool registration), not a frozen FastMCP API contract. Security risk: a coding mistake here (e.g., logging the auth token itself) would violate SG-C09's secrets-handling rule — code review should explicitly check log statements near the auth path.

## Definition of Done

Both servers run locally, pass their auth and round-trip tests, contain no duplicated logic against `server_base.py`, stay within the 150-line cap per file, and `docs/TODO.md`'s "Chunk 3" row is updated to `done`.

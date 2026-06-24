# 07 — Risks and Open Questions

## 1. Open questions requiring user confirmation (carried from `00_source_analysis.md` §3)

| ID | Question | Default if unanswered | Blocking? |
|----|----------|--------------------------|-----------|
| HW-Q01 | Which LLM provider/model to use (OpenAI/Anthropic/Gemini/Ollama)? | Pluggable `LLMClient` interface, no provider hard-wired; user supplies key via `.env` | Not blocking for skeleton; blocking for any real game run |
| HW-Q02 | Implement Tabular Q-Learning, or ship heuristic-only for v1? | Heuristic strategy first; Q-Learning as an additive stretch chunk behind the same interface | Not blocking |
| HW-Q03 | Build a GUI? | No — CLI only for v1; explicitly optional in source PDF | Not blocking |
| HW-Q04 | Cloud deployment target (Prefect Cloud / other) and tunneling mechanism? | Deferred to chunk 10; any target works as long as the 2-URL + auth contract holds | Not blocking until cloud-deploy chunk |
| HW-Q05 | Gmail/Google API OAuth credentials — who supplies them? | User must supply; cannot be fabricated | **Blocking** for HW-F21 (auto-email) to actually run |
| HW-Q06 | Who is the second group for the inter-group bonus round? | External, manual, time-boxed (≤1 week from publication); out of this repo's control | **Blocking** for HW-F27 only, not for the rest of the project |
| HW-Q07 | Are starting positions random or chosen strategically? | Configurable, random by default | Not blocking |
| HW-Q08 | Does a single local "game" (6 sub-games) keep one agent as Cop and the other as Thief throughout, or does it also do a 3-Cop-role + 3-Thief-role swap like the inter-group bonus round (HW-F27)? The HW PDF's literal "max 90 / min 30" scoring bound (§4.4, `3×20 cop + 3×10 thief`) only arises under the swapped-role aggregate; for a fixed-role match the provable bound is `cop_total ∈ [30,120]`, `thief_total ∈ [30,60]` (derivation in `docs/prds/PRD-003-dual-agent-race-logic.md`). Discovered and corrected during Chunk 5 implementation — earlier docs (PRD-003, chunk plan) incorrectly asserted the literal PDF bound applied to local matches; both have been fixed to state the corrected bound. | Engine implemented role-agnostically (it just sums whatever happened) so it is correct under either interpretation; only the Chunk 7 Internal-Game-JSON "totals" framing depends on the answer | Not blocking for Chunk 5/6 code; **should be confirmed before Chunk 7** reporting is finalized |

## 2. Technical risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| `uv` is not installed/on PATH in this environment (confirmed during Phase 0 — PyCharm references a "uv (HW6)" SDK, but the `uv` binary itself was not found in PATH) | Cannot run `uv sync`/`uv lock`/`uv run` until resolved | User must install `uv` (https://docs.astral.sh/uv/) before chunk 2 onward; `pyproject.toml` is written correctly regardless so it works the moment `uv` is available |
| Two independent LLM-backed agents communicating in free natural language is inherently non-deterministic | Test flakiness, hard-to-reproduce bugs | Decision-strategy layer and communication layer are tested separately; integration tests use seeded/mocked LLM responses, not live model calls, to keep CI deterministic |
| 150-line file cap (SG-C01) is aggressive for a stateful race engine | Risk of over-fragmenting `services/race` into too many tiny files, hurting readability | Plan explicit module boundaries up front in `docs/PLAN.md`/chunk plan rather than splitting reactively after hitting the limit |
| MCP server security (token auth + no public exposure) is easy to get wrong when deploying to cloud | Real security exposure if mis-configured during the bonus round | `services/mcp/server_base.py` centralizes auth so there is exactly one place to audit; README will document the exact deployment steps required (tunnel + auth) before the bonus round |
| Gmail API auth (OAuth, not password) is non-trivial to set up correctly | HW-F21 could be skipped or done insecurely (e.g., app password) under time pressure | PRD-005/PRD_q_learning-equivalent for reporting explicitly forbids static passwords; document exact OAuth client-secret flow in README |
| **Known limitation (Chunk 7)**: `resolve_technical_losses` (the rerun-until-6-completed algorithm) is implemented and fully tested as a standalone function, but is not yet wired into a single live match — `Hw6RaceSDK.run_local_match()` still only has Chunk 6's basic try/except containment (a failing sub-game is recorded as Technical Loss, but is not automatically retried within that same match). Wiring it in requires either reusing already-open MCP client connections across the rerun (risk: FastMCP client behavior after a context exit is unverified) or accepting a third near-duplicate of the per-sub-game loop shape (beyond the two already accepted in ADR-007) | A real run could finish with fewer than `num_games` genuinely completed sub-games if a Technical Loss occurs and is never retried | Flagged explicitly rather than silently dropped. Revisit when building the real cloud-deployed reporting flow (Chunk 10) where Technical Losses are more likely (real network MCP calls) and the cost of getting this right is more clearly justified |
| 85% coverage gate combined with "no test depends on a live external service" requires careful mocking of MCP network calls and LLM calls | Tests could become brittle or give false confidence if mocks are unrealistic | Use recorded/representative fixture responses for LLM and MCP calls in `conftest.py`, reviewed for realism per chunk |

## 3. Process risks

| Risk | Mitigation |
|------|------------|
| "Vibe coding" — agent improvising architecture instead of following PRDs (the exact failure mode the Guidelines PDF warns against) | This entire Phase 0/1 deliverable exists specifically to prevent it; no implementation chunk should begin without referencing its PRD/chunk-plan entry first |
| Documentation drift (docs say one thing, code does another) | `docs/TODO.md` and `docs/01_requirements_matrix.md` status columns must be updated in the same work session as the corresponding code change, not retroactively |

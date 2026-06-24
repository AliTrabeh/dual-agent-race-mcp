# PRD-005 — Logging, Protocol, and Observability

## Purpose

Implement the JSON reporting protocol (Internal Game JSON and Inter-Group Bonus Game JSON), Technical Loss handling, run-history logging, and the automated Gmail dispatch required at the end of every full match. This chunk is what turns a successful local run into a gradable artifact — the HW PDF is explicit and strict about this report's exact shape and delivery mechanism (HW-F21–F24).

## Scope

In scope: `services/reporting/schemas.py` (typed schema definitions for both JSON report types, matching the HW PDF's examples field-for-field), `services/reporting/run_logger.py` (accumulates per-sub-game results into the Internal Game JSON structure as the match progresses), `services/reporting/technical_loss.py` (detection + rerun-trigger logic), `services/reporting/mailer.py` (Gmail API dispatch, OAuth-based, routed through the `ApiGatekeeper`).

Out of scope: the inter-group bonus *game-play* mechanics themselves (that's PRD-003/004 run against a remote group's MCP URLs) — this chunk only covers the *reporting* of that bonus game's outcome, not negotiating or playing it.

## Requirements Covered

HW-F21 (auto-email JSON to `rmisegal+uoh26b@gmail.com` after the 6th sub-game, triggered by the Thief agent's function, via Gmail API with OAuth, not a stored password), HW-F22 (Technical Loss handling + rerun; JSON-only email body, no free text), HW-F23 (Internal Game JSON schema), HW-F24 (Inter-Group Bonus Game JSON schema), HW-F28 (bonus scoring computation: highest scorer 10pts / loser 7pts / tie 5pts each, averaged across pairings, 0 on mismatch). SG-C05/C06 (Gmail API call goes through the same `ApiGatekeeper` and rate-limit config as LLM calls). SG-C09 (OAuth credentials via `.env`, never hard-coded or stored as a plaintext password).

## Inputs and Outputs

**Inputs**: the `GameResult` produced by `RaceEngine.play_game()` (PRD-003); group metadata (`group_name`, `students`, `github_repo`, MCP URLs) sourced from `config/setup.json`; for the bonus variant, a second group's equivalent metadata.

**Outputs**: a validated Internal Game JSON document (and, when applicable, an Inter-Group Bonus Game JSON document) sent as the **entire** body of an email to the fixed grading address, plus a local copy persisted under `results/` for the README's evidence requirements.

## Components / Files Likely Needed

- `services/reporting/schemas.py` — `InternalGameReport` / `InterGroupBonusReport` typed structures (dataclass or `TypedDict`), each with a `to_json()` matching the HW PDF's literal field names exactly (`group_name`, `cop_mcp_url`, `thief_mcp_url`, `sub_games`, `totals`, etc. — see `docs/00_source_analysis.md` HW-F23/F24 for the verbatim examples).
- `services/reporting/run_logger.py` — builds up `sub_games` entries as `RaceEngine` completes each one; pure accumulation, no I/O.
- `services/reporting/technical_loss.py` — flags an incomplete/failed sub-game as `"technical_loss"`, signals the orchestrator (PRD-004) to rerun it before the report is considered final.
- `services/reporting/mailer.py` — wraps the Gmail API client; the **only** function in the whole codebase allowed to construct an outbound email; the email body is `json.dumps(report.to_json())` and nothing else (HW-F22's "JSON only, no free text" rule enforced at the single chokepoint, not scattered).

## Acceptance Criteria

- The generated Internal Game JSON validates against the exact schema in `docs/00_source_analysis.md` HW-F23 (every required key present, correct types, `totals.cop`/`totals.thief` consistent with the actual sub-game outcomes and the scoring table).
- A sub-game that failed for technical reasons (e.g., an MCP timeout, per PRD-002/004) is recorded as `"technical_loss"` and automatically rerun until 6 *completed* sub-games exist before the report is finalized — never silently reported with fewer than 6 entries.
- The email is sent exactly once per completed match, triggered specifically by code attributable to the Thief agent's responsibility per HW-F21's wording, with a body containing only the serialized JSON (verified by a test asserting the email body string is valid JSON and nothing else, e.g. no leading/trailing prose).
- Gmail API authentication uses OAuth (Google API Client / client-secret flow), never a static password — verified by code review of `mailer.py`'s auth path.

## Edge Cases

- All 6 sub-games complete but the Gmail send itself fails (network error, expired OAuth token) — must retry per the Gatekeeper's configured retry policy, not silently drop the report; on exhausted retries, must fail loudly (logged error) rather than reporting false success.
- Bonus report disagreement: if this group's bonus report and the other group's bonus report differ (HW-F28's "0 points for both sides" rule) — this codebase cannot detect a *remote* group's mismatched report on its own, since the mismatch is adjudicated externally by the grader comparing two independently-sent emails; this PRD's job is only to guarantee *this* group's report is internally consistent and sent with `mutual_agreement` accurately reflecting what was actually agreed with the other group (a value the user must supply, not fabricate).
- Re-running a Technical Loss sub-game must not double-count a previously partially-scored attempt in `totals`.

## Testing Requirements

Unit tests validating schema serialization against the HW PDF's literal example JSON (byte-for-byte field name matching). Unit tests for Technical Loss detection and rerun bookkeeping (ensuring exactly 6 final entries regardless of how many reruns occurred). Mailer tests use a fully mocked Gmail API client — no real email is ever sent during automated tests (SG-T03).

## Risks

Gmail OAuth setup is a real external dependency the assistant cannot fabricate credentials for (flagged as blocking HW-Q05 in `docs/07_risks_and_open_questions.md`) — this chunk can be fully built and unit-tested with mocks, but an actual end-to-end email send requires the user to supply real OAuth client credentials via `.env`.

## Definition of Done

Schema tests pass against the literal PDF examples, Technical Loss/rerun logic is tested, mailer logic is tested with mocks, all files ≤150 lines, and `docs/TODO.md`'s "Chunk 7" row updated to `done`.

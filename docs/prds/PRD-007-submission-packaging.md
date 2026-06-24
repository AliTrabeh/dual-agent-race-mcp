# PRD-007 — Submission Packaging

## Purpose

Turn a working, tested codebase into a graded-ready submission: finalize the scientific README, deploy MCP servers to the cloud, prepare for (and document) the inter-group bonus round, and run the final checklist from `docs/06_submission_checklist.md` against both governing PDFs. This chunk is explicitly about packaging and process, not new application logic.

## Scope

In scope: finalizing root `README.md` to full academic-write-up standard (Dec-POMDP tuple, orchestration discussion, learning-curve visuals if applicable, CLI evidence, deployment instructions), cloud deployment of both MCP servers behind auth (HW-F16 stage 2), preparing the exact 2 URLs + GitHub repo link needed for HW-F18/F26, and documenting the inter-group bonus round process (HW-F27/F28) so the user can execute it within the 1-week window even though this repo cannot execute it standalone.

Out of scope: actually finding/pairing with a second student group and running the bonus match — external, manual, time-boxed, owned by the user (HW-Q06 in `docs/07_risks_and_open_questions.md`).

## Requirements Covered

HW-F16 (3-stage rollout — this chunk executes stage 2 and prepares stage 3), HW-F26 (full submission format: GitHub repo + scientific README), HW-F27/F28 (bonus round mechanics and scoring — documented and report-schema-ready, even if not played during this session). SG-D01 (full user-manual README). SG-U03 (git workflow: branches, PRs, release tags — applied at this packaging stage). All of `docs/06_submission_checklist.md` sections A and B.

## Inputs and Outputs

**Inputs**: the completed, tested codebase from chunks 0–9; the user's choice of cloud platform/tunneling mechanism (HW-Q04, not prescribed by this PRD); real LLM and Gmail credentials supplied by the user.

**Outputs**: a publicly accessible GitHub repository at submission time; two live, authenticated MCP server URLs; a finalized `README.md`; a populated `docs/06_submission_checklist.md` with every box checked or explicitly justified as not applicable.

## Components / Files Likely Needed

- Root `README.md` — final pass, incorporating actual results (not placeholder text) once chunks 0–9 have produced real run output.
- Deployment notes (could live in `README.md`'s "Deployment" section, or a dedicated `docs/deployment.md` if it grows large) covering exactly which of the 3 cloud-exposure mechanisms (ngrok / Localtonet / Nginx reverse proxy, or a managed platform like Prefect Cloud) was chosen and how auth was configured.
- No new `src/` modules are anticipated; if cloud deployment surfaces a real bug (e.g., a hard-coded `localhost` assumption), the fix belongs in the relevant earlier chunk's module, not bolted on here.

## Acceptance Criteria

- README contains the formal Dec-POMDP tuple mapped explicitly to this project's classes/modules (not just the abstract definition).
- README's install/run/test instructions work verbatim when followed top-to-bottom on a clean checkout (this is itself testable — a "fresh clone smoke test").
- Both MCP server URLs are reachable only with a valid auth token; an unauthenticated probe is rejected (verified manually or via a scripted check against the live deployment, not just unit tests against local code).
- Every item in `docs/06_submission_checklist.md` is either checked or has an explicit, documented reason it doesn't apply (e.g., "GUI not built — optional per HW PDF").

## Edge Cases

- Cloud platform free-tier limits or cold-start latency could cause an MCP call to time out during the actual bonus round — document a recommended retry/backoff expectation in the README so this doesn't silently look like a Technical Loss caused by a bug.
- If the user decides not to implement Q-Learning or a GUI, the README must still read coherently — explicitly state these were optional per the HW PDF and were deliberately deprioritized in favor of orchestration quality (HW-F03), not omitted by oversight.

## Testing Requirements

A "fresh clone" smoke test: clone the repo to a new directory, run `uv sync`, `uv run pytest`, `uv run python -m hw6_race.main` (or equivalent), confirm it works without any machine-specific state from the development environment leaking in (e.g., absolute paths, personal API keys committed by accident — re-checked against `.gitignore`/`.env-example` rules from SG-C09).

## Risks

This chunk is where previously-deferred external dependencies (real LLM keys, real Gmail OAuth, a real second group for the bonus round) all come due at once — if any of HW-Q01/Q05/Q06 from `docs/07_risks_and_open_questions.md` remain unresolved by this point, this chunk cannot be fully completed and must be explicitly marked partial in `docs/TODO.md`, not silently skipped.

## Definition of Done

`docs/06_submission_checklist.md` fully checked (or justified), README finalized and verified via fresh-clone smoke test, MCP servers live and authenticated in the cloud, and `docs/TODO.md`'s "Chunk 10" and "Chunk 11" rows updated to `done`.

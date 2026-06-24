# PRD-006 — Testing and Validation

## Purpose

Stand up the full test suite — unit, integration, staged sanity checks, coverage gate, and linting — as its own tracked chunk rather than an afterthought, even though individual tests are written alongside each implementation chunk per TDD (SG-T01). This chunk's job is to make sure the *suite as a whole* satisfies the Guidelines PDF's hard gates (≥85% coverage, 0 ruff warnings) and the HW PDF's staged sanity-check requirement (HW-F12), and to produce the test-result reporting artifact required by SG-T06.

## Scope

In scope: `tests/conftest.py` finalization (shared fixtures used across all modules — fake clock, mocked `LLMClient`, mocked Gmail client, ephemeral MCP test servers), `tests/integration/test_staged_sanity_checks.py` (parametrized 2×2/3×3/4×4/5×5 grid runs), coverage configuration verification, ruff configuration verification, and a consolidated test-run report.

Out of scope: writing the *first* unit test for any given module — those are written per-chunk, alongside that module's implementation (TDD), not deferred to this chunk. This chunk is about suite-level completeness and the gate checks, not individual test authorship.

## Requirements Covered

HW-F12 (staged sanity checks across grid sizes). SG-T01 (TDD process — audited here, not enforced by tooling). SG-T02 (every module has matching tests; every public function has ≥1 test — audited via coverage report, not just raw percentage). SG-T03 (test layout, mocking, no live external dependencies). SG-T04 (≥85% global coverage, enforced via `pyproject.toml` `fail_under=85`). SG-T05 (edge cases documented — see `docs/05_testing_strategy.md` §4). SG-T06 (test result reporting). SG-T07 (ruff 0 warnings).

## Inputs and Outputs

**Inputs**: the full `src/` tree as it exists after chunks 0–8 land; the edge-case register in `docs/05_testing_strategy.md`.

**Outputs**: a passing `uv run pytest --cov=src --cov-report=term-missing tests/` run at ≥85% coverage; a passing `uv run ruff check src/ tests/` with 0 warnings; a recorded pass/fail/coverage summary appended to `docs/08_claude_work_log.md`.

## Components / Files Likely Needed

- `tests/conftest.py` — central fixture file; must not become a dumping ground (keep ≤150 lines, split into `tests/fixtures/` helper modules if it grows past that).
- `tests/integration/test_staged_sanity_checks.py` — parametrized over the 4 stages in `docs/05_testing_strategy.md` §2.
- `tests/integration/test_full_local_match.py` — the single most important integration test: a complete 6-sub-game run via `Hw6RaceSDK.run_local_match()`, fully mocked at the LLM/Gmail boundary, real at the race-engine/MCP-transport boundary.
- No new `src/` production code is expected from this chunk — it is allowed to surface bugs in earlier chunks, which then get fixed in those chunks' modules (with a note added to `docs/TODO.md` cross-referencing back).

## Acceptance Criteria

- `pytest --cov` reports ≥85% on `src/`, excluding `src/main.py` and any future `src/**/gui/*` per the Guidelines PDF's own `omit` list.
- `ruff check` reports 0 warnings across the entire `src/` and `tests/` trees.
- All 4 staged sanity-check grid sizes run to completion without unhandled exceptions.
- The full local match integration test passes deterministically on repeated runs (no flakiness from unmocked randomness — any randomness, e.g. random start positions, must be seeded in tests).

## Edge Cases

- A module that's hard to reach 85% coverage on individually (e.g., error branches in `mailer.py`'s retry-exhaustion path) — must still be tested via fault injection on the mocked Gmail client, not excluded from coverage just because it's inconvenient.
- Flaky integration tests due to real threads/async timing in the MCP layer — mitigated by using FastMCP's in-process test utilities rather than real sockets wherever possible, per PRD-002.

## Testing Requirements

This PRD *is* the testing requirements document for the project as a whole; see `docs/05_testing_strategy.md` for the full strategy narrative and edge-case register, which this chunk operationalizes.

## Risks

There is tension between SG-C01 (≤150 lines/file, encouraging many small files) and SG-T04 (≥85% coverage, which is easier to hit when files are cohesive and fully exercised) — the resolution is to make sure every small file still gets its own focused test file (SG-T03's mirroring rule), rather than letting fragmentation create untested seams between files.

## Definition of Done

Coverage and lint gates both pass cleanly, the staged sanity-check matrix and full-match integration test both pass, and a results summary is appended to `docs/08_claude_work_log.md` with the actual coverage percentage and ruff output. `docs/TODO.md`'s "Chunk 9" row updated to `done`.

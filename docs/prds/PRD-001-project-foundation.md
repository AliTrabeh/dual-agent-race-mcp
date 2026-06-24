# PRD-001 — Project Foundation

## Purpose

Establish the foundational project scaffold — package layout, dependency management, configuration system, versioning, and the API Gatekeeper — that every other chunk depends on. Nothing in chunks 3–10 can be built correctly without this chunk being right first, because the Guidelines PDF treats these as hard gates (SDK architecture, `uv`-only tooling, centralized config, no magic values) rather than nice-to-haves. Getting this chunk wrong propagates structural debt through the entire submission.

## Scope

In scope: `pyproject.toml` (uv-based, no `requirements.txt`), the `src/hw6_race` package skeleton with `sdk/`, `shared/`, `services/` subpackages and their `__init__.py` files, `constants.py`, `shared/config.py` (config loader/validator), `shared/version.py` (SG-C10 versioning), `shared/gatekeeper.py` (the `ApiGatekeeper`), `config/setup.json` and `config/rate_limits.json`, `.env-example`, `.gitignore`, and the root `tests/conftest.py` shared fixtures scaffold.

Out of scope: any game-domain logic (race state, MCP servers, agents) — those belong to chunks 3–6. This chunk produces *infrastructure only*.

## Requirements Covered

HW-F06, HW-F25 (config centralization); SG-C03 (SDK as single entry point — scaffold only, populated later); SG-C05/C06/C07 (API Gatekeeper + rate limits + queueing); SG-C08 (no magic values — `constants.py` exists from day one); SG-C09 (config hierarchy + secrets via `.env`); SG-C10 (versioning starts at 1.00); SG-C11 (package hygiene: `__init__.py`, `__all__`, `__version__`, no circular imports); SG-U01/U02 (uv-only, `pyproject.toml` as single source of truth, no `requirements.txt`).

## Inputs and Outputs

**Inputs**: the requirements matrix (`docs/01_requirements_matrix.md`), the canonical layout it defines, and the rate-limit/config schemas reproduced verbatim from the Guidelines PDF.

**Outputs**: a project that `uv sync` can install cleanly (once `uv` is available — see risk below), whose packages all import without error, and whose `shared/gatekeeper.py` exposes exactly the interface shown in the Guidelines PDF (`__init__(config: RateLimitConfig)`, `execute(api_call, *args, **kwargs)`, `get_queue_status() -> QueueStatus`).

## Components / Files Likely Needed

- `pyproject.toml` — project metadata, dependencies, `[tool.ruff]`, `[tool.coverage.run]`, `[tool.coverage.report]` sections matching the Guidelines PDF's exact config blocks.
- `src/hw6_race/__init__.py`, `constants.py`, `main.py` (thin CLI entry stub for now).
- `src/hw6_race/shared/{__init__.py, config.py, version.py, gatekeeper.py}`.
- `src/hw6_race/sdk/{__init__.py, sdk.py}` (empty-but-importable for now).
- `src/hw6_race/services/__init__.py` (subpackages added in later chunks).
- `config/setup.json`, `config/rate_limits.json`.
- `.env-example`, `.gitignore`.
- `tests/conftest.py`, `tests/unit/test_shared/{test_config.py, test_version.py, test_gatekeeper.py}`.

## Acceptance Criteria

- `import hw6_race` and `import hw6_race.shared.gatekeeper` succeed with no side effects beyond logging setup.
- `shared/version.py` reports `1.00` (or `"1.00"`, matching the JSON string convention used elsewhere) as the current version, importable as a constant.
- `config/setup.json` and `config/rate_limits.json` both contain a `"version": "1.00"` key.
- `ApiGatekeeper.get_queue_status()` returns a well-typed result even with zero calls made.
- No file in this chunk exceeds 150 logical lines.
- `ruff check src/` reports 0 warnings for everything created in this chunk.

## Edge Cases

- Config file missing or malformed JSON → `shared/config.py` raises a clear, typed exception rather than a raw `KeyError`/`json.JSONDecodeError` leaking to the caller.
- `.env` not present at all (first-time setup) → `.env-example` must still allow the app to start in a "no external calls configured" mode rather than crashing at import time.
- Rate limit config missing a service entry → Gatekeeper falls back to the `"default"` service block shown in the Guidelines PDF example, not a silent no-limit bypass.

## Testing Requirements

Unit tests for `shared/config.py` (valid load, missing file, malformed JSON), `shared/version.py` (returns expected string/format), `shared/gatekeeper.py` (rate limit enforcement, queueing, retry-after, backpressure at max depth) — all using a fake clock, no real `time.sleep`. These are the first tests written in the project and establish the `conftest.py` fixture patterns (e.g. a `tmp_config_dir` fixture) that later chunks reuse.

## Risks

`uv` was confirmed not installed/on PATH in this environment during Phase 0 (see `docs/07_risks_and_open_questions.md`). This chunk produces a `pyproject.toml` that is correct for `uv` regardless, but cannot be validated end-to-end with `uv sync`/`uv lock` until the user installs `uv`. In the interim, `python -m pytest`/`pip`-free manual verification is acceptable for the assistant's own validation, but the **committed** instructions and CI-equivalent commands must always be the `uv` forms per SG-U01.

## Definition of Done

All files above exist, import cleanly, pass their unit tests, pass `ruff check` with 0 warnings, and `docs/TODO.md`'s "Chunk 2" row is updated to `done` with this PRD referenced.

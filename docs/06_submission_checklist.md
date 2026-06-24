# 06 — Submission Checklist

Merged from the HW PDF's submission requirements (§11, §13) and the Guidelines PDF's final checklist (§17) and quick-reference table (§19). Check every box before declaring the project submission-ready. This file is updated, not rewritten, as chunks complete. Updated as of Chunk 10.

## A. HW PDF requirements

- [x] Public GitHub repo contains all source code — `github.com/AliTrabeh/dual-agent-race-mcp`
- [x] Root `README.md` is a high-academic-language scientific write-up (not just a how-to) — finalized in Chunk 10
- [x] README states the formal Dec-POMDP tuple `⟨n, S, {Ai}, P, R, {Ωi}, O, γ⟩` mapped explicitly to this game — README §1
- [x] README discusses orchestration challenges: free NL coordination, no rigid protocol, ambiguity handling, mutual-understanding strategy — README §2
- [ ] README includes learning-curve visualization/proof **if** Q-Learning was used — **N/A**: Q-Learning not implemented (explicitly optional per HW-F20; heuristic strategy used instead, per HW-F03's priority on orchestration over strategy quality)
- [ ] README/repo includes logs from the inter-group bonus MCP servers **if** the bonus round was played — **N/A**: bonus round not yet played (requires pairing with a second group, HW-Q06)
- [x] README/repo includes CLI run evidence (Q-table or heuristic decision trace) — README §5, real captured output
- [ ] README/repo includes a GUI screen-capture **if** a GUI was built — **N/A**: no GUI built (explicitly optional; discussed with user, deferred until after required chunks)
- [x] `config.json`/`config.yaml` centralizes all game parameters — zero hard-coded game constants — `config/setup.json`
- [ ] Exactly 2 MCP URLs available per group (Cop, Thief) — local for dev, cloud for submission/bonus — **local: done** (in-process servers); **cloud: pending** — requires a real cloud account, documented as an actionable guide in README §8, not yet performed
- [x] Token-based auth + revoke implemented on both MCP servers — `services/mcp/auth.py`, tested in Chunk 3
- [ ] No MCP server fully exposed to the public internet without firewall/auth protection — **not yet applicable**: servers are not yet deployed to any public network (Stage 1, local-only); the auth mechanism itself is implemented and tested, ready for Stage 2
- [ ] Internal Game JSON emailed automatically to `rmisegal+uoh26b@gmail.com` after the 6th sub-game, by the Thief agent's function — **partial**: `InternalGameReport`/`ReportMailer` implemented and tested (Chunk 7) but not yet wired into the CLI's default live-match path; real Gmail OAuth credentials are also not yet supplied (HW-Q05) — see `docs/07_risks_and_open_questions.md`
- [x] Email body contains **only** the JSON — no free text — enforced at the single `ReportMailer.send_report()` chokepoint, tested
- [ ] Technical Loss sub-games are rerun, not left incomplete — **partial**: `resolve_technical_losses()` is implemented and tested as a standalone algorithm (Chunk 7) but not yet wired into a single live match — flagged as a known limitation, not silently dropped
- [ ] (If bonus round played) Inter-Group Bonus Game JSON sent independently by both groups, with matching data — **N/A**: bonus round not yet played

## B. Guidelines PDF — mandatory docs & structure

- [x] `README.md` at repo root, full user-manual level (install/usage/examples/config guide/contribution/license)
- [x] `docs/PRD.md`, `docs/PLAN.md`, `docs/TODO.md` present and reflect actual current state
- [x] `docs/PRD_<mechanism>.md` present for every significant algorithm/mechanism (`docs/PRD_q_learning.md`)
- [x] Canonical project layout followed (`src/<pkg>/{sdk,shared,services}`, `tests/`, `config/`, `docs/`, etc.)
- [x] Prompt Engineering Log maintained (`docs/08_claude_work_log.md`) — 10 entries as of Chunk 10

## C. Guidelines PDF — code & architecture

- [x] All files ≤150 logical lines — actually held to a stricter ≤150 *physical*-line project rule (PROJ-R01)
- [x] Docstrings explain *why*; SRP + DRY enforced; meaningful names throughout
- [x] SDK is the single entry point for all business logic; CLI/GUI contain none — `Hw6RaceSDK`, verified in Chunk 8 code review
- [x] Zero tolerated code duplication; mixins/base classes used where 2+ identical patterns would otherwise appear — one explicitly documented, justified exception (ADR-007 in `docs/PLAN.md`: two thin per-sub-game loop shapes, sync scripted-testing vs. async real-MCP)
- [x] `ApiGatekeeper` intercepts all outbound API calls (LLM + Gmail); rate limits centralized in `config/rate_limits.json`
- [x] FIFO queue + backpressure alert + retry implemented for rate-limited calls — tested in Chunk 2
- [x] Zero magic values in source — all via `constants.py`, config, or `Enum`s
- [x] `.env` used for secrets, `.env-example` committed with placeholders, `.gitignore` excludes `.env`/`*.key`/`*.pem`/`credentials.json`
- [x] Versioning starts at 1.00 and is tracked in `shared/version.py` + JSON `version` keys
- [x] Package hygiene: every package has `__init__.py` with `__all__`/`__version__`; no circular imports

## D. Guidelines PDF — testing & tooling

- [x] TDD followed (Red-Green-Refactor) — verifiable via `docs/08_claude_work_log.md`'s per-chunk entries
- [x] Test coverage ≥85% globally (`pytest --cov`) — 100.00% as of Chunk 9/10
- [x] `ruff check` reports 0 warnings
- [x] Edge cases documented and tested (see `docs/05_testing_strategy.md`)
- [x] All dependency/build/test/run commands go through `uv` (`uv sync`, `uv add`, `uv run python`, `uv run pytest`, `uv lock`) — no `pip`, no `requirements.txt` — confirmed via an actual fresh-clone smoke test (Chunk 10), which caught and fixed a real bug: dev tooling was declared under `[project.optional-dependencies]` (not installed by plain `uv sync`) rather than `[dependency-groups]` (installed by default) — see `docs/07_risks_and_open_questions.md`
- [x] `pyproject.toml` is the single dependency source of truth; `uv.lock` exists and is committed
- [ ] Git history is meaningful; feature branches + PRs + release tags used — **honest gap**: commit messages are meaningful and one-per-chunk (per the user's explicit workflow request), but all work has gone directly to `main` with no feature branches, no PRs, and no release tags. This is a real, acknowledged deviation from SG-U03, not silently glossed over — revisit before final submission if a stricter git workflow is desired

## E. Quick-reference gate table (verbatim source: Guidelines PDF p.33)

| Gate | Threshold | Verification | Status (as of Chunk 10) |
|------|-----------|----------------|----------------------------|
| SDK architecture | All logic via SDK | Code review | ✅ Pass |
| OOP/no duplication | ≤1 repeated pattern | Code review | ✅ Pass (1 documented exception, ADR-007) |
| API Gatekeeper | All external calls routed | Code review + test | ✅ Pass |
| Rate limits | Centralized | Config check | ✅ Pass |
| Pagination/queueing | — | Integration test | ✅ Pass |
| Versioning | Starts at 1.00 | Module check | ✅ Pass |
| TDD | Red-Green-Refactor | Process review | ✅ Pass |
| File size | ≤150 lines | Automated check | ✅ Pass (`tests/test_line_limits.py`) |
| Linter | 0 warnings | `ruff check` | ✅ Pass |
| Coverage | ≥85% | `pytest --cov` | ✅ Pass (100.00%) |
| Magic values | 0 | Code review | ✅ Pass |
| Secrets | `.env-example`, 0 in code | Automated scan | ✅ Pass |
| Dependency manager | `uv` only | Automated check | ✅ Pass |

## F. Project-specific session constraints (not from either PDF — see `docs/00_source_analysis.md` §9a)

- [x] Python file line limit: every `.py` file under `src/`, `tests/`, `tools/` is ≤150 physical lines — verified by `tests/test_line_limits.py`
- [x] PRD count: project contains ≥510 PRDs — 522 in `docs/prds/catalog/` plus 7 detailed PRDs plus `docs/PRD.md`/`docs/PRD_q_learning.md`
- [x] Tests pass: `uv run pytest tests/` reports 217/217 passing, 100% coverage, and `uv run ruff check` reports 0 warnings, confirmed via the real `uv` toolchain as of Chunk 9/10

## G. Summary of remaining gaps (honest, not hidden)

| Gap | Why it remains open | Blocking for submission? |
|-----|----------------------|------------------------------|
| Cloud deployment (Stage 2) | Requires a real cloud account/credentials — actionable guide written (README §8), not performed | Only if the assignment requires the cloud URLs to already be live at submission time — re-check assignment deadline vs. this repo's state |
| Auto-email wiring + real Gmail OAuth | `ReportMailer`/`InternalGameReport` implemented + tested; not connected to the CLI's default path; real OAuth credentials are user-supplied (HW-Q05) | Yes, for HW-F21 specifically — needs the user's action |
| Technical-Loss rerun wired into a live match | Algorithm implemented + tested standalone; not yet integrated end-to-end (known limitation, `docs/07_risks_and_open_questions.md`) | Only if a real run actually produces a Technical Loss — unlikely under normal operation, but not impossible over real network calls |
| Inter-group bonus round | Requires pairing with a second group within 1 week of publication (HW-Q06) | External, time-boxed, out of this repo's control |
| Git workflow (branches/PRs/tags) | All work committed directly to `main`, per the user's explicit per-chunk workflow request | Not blocking for code correctness; a process-only gap |
| Optional Q-Learning / GUI | Both explicitly optional per the HW PDF; descoped by user decision to finish required chunks first | No |

## H. ISO/IEC 25010 self-check (SG-C14, recommended self-assessment, not a hard gate)

| Characteristic | Self-assessment | Evidence |
|------------------|---------------------|------------|
| Functional Suitability | Strong | Every HW PDF functional requirement (HW-F01–F29) is traced in `docs/01_requirements_matrix.md`; all but externally-blocked items (cloud deploy, bonus round, Gmail OAuth) are implemented and tested |
| Performance Efficiency | Adequate for an academic match (≤25 moves × 6 sub-games); no profiling performed — not a stated requirement, and the in-process MCP/async design avoids obvious bottlenecks |
| Compatibility | Pure Python 3.11+, FastMCP, no OS-specific code paths observed; developed and validated on Windows |
| Usability | CLI has `--help`, `--dry-run`, clear exit codes, and a readable per-turn trace; no GUI (optional, not built) |
| Reliability | 217/217 tests pass deterministically (no flaky tests observed across ~15 full runs this session); graceful degradation verified live under real rate-limit pressure (Chunk 6/8 logs) |
| Security | Token-based MCP auth + revoke; secrets only via `.env`/`os.environ`; `.gitignore` excludes all secret file patterns; Gmail dispatch is OAuth-only by design (never a stored password) |
| Maintainability | 100% test coverage, 0 ruff warnings, every file ≤150 physical lines, SDK-only entry point, zero tolerated duplication (1 documented exception, ADR-007) |
| Portability | `uv`-managed, single `pyproject.toml` source of truth, no hard-coded absolute paths in source (confirmed via two independent fresh-clone tests, Chunk 10) |

**Overall**: the codebase scores strongly on the characteristics fully within its control (functional suitability, maintainability, security, reliability); Performance Efficiency and Compatibility are adequate-but-unmeasured since the assignment doesn't require benchmarking; Portability was concretely *proven*, not just claimed, via the fresh-clone smoke test.

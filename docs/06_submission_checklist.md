# 06 — Submission Checklist

Merged from the HW PDF's submission requirements (§11, §13) and the Guidelines PDF's final checklist (§17) and quick-reference table (§19). Check every box before declaring the project submission-ready. This file is updated, not rewritten, as chunks complete.

## A. HW PDF requirements

- [ ] Public GitHub repo contains all source code
- [ ] Root `README.md` is a high-academic-language scientific write-up (not just a how-to)
- [ ] README states the formal Dec-POMDP tuple `⟨n, S, {Ai}, P, R, {Ωi}, O, γ⟩` mapped explicitly to this game
- [ ] README discusses orchestration challenges: free NL coordination, no rigid protocol, ambiguity handling, mutual-understanding strategy
- [ ] README includes learning-curve visualization/proof **if** Q-Learning was used (optional)
- [ ] README/repo includes logs from the inter-group bonus MCP servers **if** the bonus round was played
- [ ] README/repo includes CLI run evidence (Q-table or heuristic decision trace)
- [ ] README/repo includes a GUI screen-capture **if** a GUI was built (optional)
- [ ] `config.json`/`config.yaml` centralizes all game parameters — zero hard-coded game constants
- [ ] Exactly 2 MCP URLs available per group (Cop, Thief) — local for dev, cloud for submission/bonus
- [ ] Token-based auth + revoke implemented on both MCP servers
- [ ] No MCP server fully exposed to the public internet without firewall/auth protection
- [ ] Internal Game JSON emailed automatically to `rmisegal+uoh26b@gmail.com` after the 6th sub-game, by the Thief agent's function
- [ ] Email body contains **only** the JSON — no free text
- [ ] Technical Loss sub-games are rerun, not left incomplete
- [ ] (If bonus round played) Inter-Group Bonus Game JSON sent independently by both groups, with matching data

## B. Guidelines PDF — mandatory docs & structure

- [ ] `README.md` at repo root, full user-manual level (install/usage/examples/config guide/contribution/license)
- [ ] `docs/PRD.md`, `docs/PLAN.md`, `docs/TODO.md` present and reflect actual current state
- [ ] `docs/PRD_<mechanism>.md` present for every significant algorithm/mechanism (at minimum `PRD_q_learning.md` if RL is implemented)
- [ ] Canonical project layout followed (`src/<pkg>/{sdk,shared,services}`, `tests/`, `config/`, `docs/`, etc.)
- [ ] Prompt Engineering Log maintained (`docs/08_claude_work_log.md`)

## C. Guidelines PDF — code & architecture

- [ ] All files ≤150 logical lines
- [ ] Docstrings explain *why*; SRP + DRY enforced; meaningful names throughout
- [ ] SDK is the single entry point for all business logic; CLI/GUI contain none
- [ ] Zero tolerated code duplication; mixins/base classes used where 2+ identical patterns would otherwise appear
- [ ] `ApiGatekeeper` intercepts all outbound API calls (LLM + Gmail); rate limits centralized in `config/rate_limits.json`
- [ ] FIFO queue + backpressure alert + retry implemented for rate-limited calls
- [ ] Zero magic values in source — all via `constants.py`, config, or `Enum`s
- [ ] `.env` used for secrets, `.env-example` committed with placeholders, `.gitignore` excludes `.env`/`*.key`/`*.pem`/`credentials.json`
- [ ] Versioning starts at 1.00 and is tracked in `shared/version.py` + JSON `version` keys
- [ ] Package hygiene: every package has `__init__.py` with `__all__`/`__version__`; no circular imports

## D. Guidelines PDF — testing & tooling

- [ ] TDD followed (Red-Green-Refactor) — verifiable via commit history/process notes
- [ ] Test coverage ≥85% globally (`pytest --cov`)
- [ ] `ruff check` reports 0 warnings
- [ ] Edge cases documented and tested (see `docs/05_testing_strategy.md`)
- [ ] All dependency/build/test/run commands go through `uv` (`uv sync`, `uv add`, `uv run python`, `uv run pytest`, `uv lock`) — no `pip`, no `requirements.txt`
- [ ] `pyproject.toml` is the single dependency source of truth; `uv.lock` exists and is committed
- [ ] Git history is meaningful; feature branches + PRs + release tags used

## E. Quick-reference gate table (verbatim source: Guidelines PDF p.33)

| Gate | Threshold | Verification |
|------|-----------|----------------|
| SDK architecture | All logic via SDK | Code review |
| OOP/no duplication | ≤1 repeated pattern | Code review |
| API Gatekeeper | All external calls routed | Code review + test |
| Rate limits | Centralized | Config check |
| Pagination/queueing | — | Integration test |
| Versioning | Starts at 1.00 | Module check |
| TDD | Red-Green-Refactor | Process review |
| File size | ≤150 lines | Automated check |
| Linter | 0 warnings | `ruff check` |
| Coverage | ≥85% | `pytest --cov` |
| Magic values | 0 | Code review |
| Secrets | `.env-example`, 0 in code | Automated scan |
| Dependency manager | `uv` only | Automated check |

## F. Project-specific session constraints (not from either PDF — see `docs/00_source_analysis.md` §9a)

- [x] Python file line limit: every `.py` file under `src/`, `tests/`, `tools/` is ≤150 physical lines — verified by `tests/test_line_limits.py` (currently passing, largest file 87 lines)
- [x] PRD count: project contains ≥510 PRDs — verified by counting `docs/prds/catalog/PRD-*.md` (currently 522) plus the 7 detailed PRDs in `docs/prds/` and `docs/PRD.md`/`docs/PRD_q_learning.md`
- [x] Tests pass: `uv run pytest tests/` (validated via `python -m pytest` pending `uv` install) reports all tests passing, ≥85% coverage, and `ruff check` reports 0 warnings, at the time this box was checked

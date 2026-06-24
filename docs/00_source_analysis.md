# 00 — Source Document Analysis

This document is the canonical extraction of every requirement found in the two governing PDFs. All other planning documents (PRDs, architecture, chunk plan) must trace back to items listed here. Where the source text is ambiguous, the item is marked **[Needs confirmation]**.

Source documents (do not delete, do not modify):
- `ex06-Dual AI agent race via MCP servers.pdf` — 17 pages, Hebrew, v1.0, dated 2026-06-19 (the "HW PDF")
- `software_submission_guidelines-V3.pdf` — 39 pages, Hebrew/English, v3.00, dated 2026-03-26 (the "Guidelines PDF")

---

## 1. HW PDF — Functional Requirements

| ID | Requirement | Source (page) |
|----|-------------|----------------|
| HW-F01 | Build a complete game pipeline allowing two independent AI agents — "Cop" and "Thief" — to play a pursuit game on a 2D grid against each other, fully autonomously via MCP servers, no human intervention. | p.2-3 |
| HW-F02 | Each agent must: (1) decode the other's messages, written in natural language; (2) infer the opponent's likely location from partial observability; (3) translate conclusions into physical grid moves. | p.3 |
| HW-F03 | Success is measured by the orchestration/communication ability of the agent pair, **not** by which strategy/algorithm wins. | p.3 |
| HW-F04 | A sub-game is a single pursuit episode on the grid, capped at 25 moves. Players alternate turns, Thief moves first, then Cop, repeating. | p.3 |
| HW-F05 | A game = a sequence of 6 sub-games played back-to-back; results accumulate and are reported together at the end. | p.3 |
| HW-F06 | Grid default size is 5×5, but the grid size must be configurable via the configuration file (dynamic, not hard-coded). | p.4 |
| HW-F07 | Cop and Thief start at grid positions — either random or chosen as strategy. Movement allowed in all 4 directions (no diagonal). Game state = full grid state, changes each move. | p.4 |
| HW-F08 | Cop wins a sub-game when it reaches exactly the cell the Thief occupies (capture). | p.4 |
| HW-F09 | Thief wins a sub-game if it survives all 25 moves without the Cop landing on its cell. | p.4 |
| HW-F10 | Barriers: as an alternative action to moving, the Cop may place a barrier on the cell it currently occupies. A barrier prevents the Cop from advancing through it on a later move, but does **not** block the Thief (one-way blocking, like a wall/board edge for the Cop only). Cop is limited to a maximum of 5 barriers per sub-game; the Thief may not place barriers at all. | p.4 |
| HW-F11 | Scoring per sub-game: Cop win → Cop 20 / Thief 5. Thief win → Thief 10 / Cop 5. Max total per full game (6 sub-games) = 90 pts (3×20 cop + 3×10 thief); min = 30 pts. | p.4 |
| HW-F12 | Staged sanity checks recommended across increasing grid sizes/complexity: Stage 1 (2×2, algorithmic sanity, minimal Pipeline integration) → Stage 2 (3×3/3×2, coordination & hyperparameter checks) → Stage 3 (4×4/4×3, partial-observability effects) → Stage 4 (5×5, final full test run, graphs, full result analysis). | p.5 |
| HW-F13 | Two independent MCP servers, one per agent (Cop server, Thief server). Servers do not exchange direct in-memory locations — only free natural-language text messages. | p.5-6 |
| HW-F14 | Each agent has its own MCP server built with **FastMCP**, exposing tools to the outside world for: mutual message authentication, sending positions/messages, receiving them. | p.5-6 |
| HW-F15 | Architecture: LLM is decoupled from / not housed inside the MCP server. MCP Client = the game engine/orchestrator that calls Tool Call on the MCP server and routes the result back to its LLM for the next decision step. | p.6 |
| HW-F16 | 3-stage rollout: (1) local: run both servers on localhost on separate ports; (2) cloud: deploy MCP servers to a cloud platform (e.g. Prefect Cloud) after local pipeline is verified; (3) inter-group bonus competition between deployed cloud servers. | p.6 |
| HW-F17 | Authentication & security: must implement a token-based auth mechanism with revoke capability to prevent unauthorized third-party access; MCP server URLs must not be fully open to the public internet without a firewall/protection layer. Don't run/test servers directly from the dev machine on non-standard exposed ports on hardened organizational networks. | p.6-7 |
| HW-F18 | Each group needs exactly 2 URLs — one for the Cop MCP server, one for the Thief MCP server. | p.6 |
| HW-F19 | 3 architectures for connecting the LLM: (1) public cloud API key (OpenAI/Anthropic/Gemini) — simplest, recommended; (2) local Ollama exposed via secure tunnel (ngrok / Localtonet / Nginx reverse proxy) with auth; (3) hybrid — keep Ollama local (loopback only), only the MCP server goes to the cloud, client makes outbound-only HTTPS calls to it (recommended for secure local dev). | p.7-8 |
| HW-F20 | Recommended (**optional**, not mandatory) RL algorithm: Tabular Q-Learning with Bellman-equation update, epsilon-greedy policy, state = grid position index, action = 4 movement directions, reward per the scoring table. Reference implementation given in the PDF (numpy Q-table, `update_q_table` function). Heuristic/min-distance/prompt-engineering-only decision making is an acceptable alternative. | p.8-10 |
| HW-F21 | At the end of all sub-games, the Thief agent (specifically) must automatically execute a function that emails a single summary report to `rmisegal+uoh26b@gmail.com`. Recommended technology: Gmail API via Google API Client, with non-password-based auth (single/multi-use temporary token via OAuth/Google Console client secret), not a stored static password. | p.10 |
| HW-F22 | Two extra report rules: (a) sub-games that don't complete due to technical failure are "Technical Loss" and must be rerun to complete the set of 6; (b) the email body must contain **only** the JSON report — no free text — to allow automated ingestion by the grading system. | p.10 |
| HW-F23 | "Internal Game JSON" report structure (per group, sent independently): fields `group_name`, `students`, `github_repo`, `cop_mcp_url`, `thief_mcp_url`, `timezone`, `sub_games`, `totals.cop`, `totals.thief`. Exact example given p.11. | p.10-11 |
| HW-F24 | "Inter-Group Bonus Game JSON" report structure (sent once per pair after bonus game): fields `report_type`, `groups.group_1/2`, `github_repo_group_1/2`, `mcp_url_group_1/2_cop/thief`, `timezone`, `students_group_1/2`, `sub_games`, `totals_by_group`, `bonus_claim`, `mutual_agreement`. Exact example given p.11-12. | p.11-12 |
| HW-F25 | Configuration file (`config.json` or `config.yaml`) is **mandatory** and must centralize **all** game parameters — hard-coding game parameters is strictly forbidden. Required keys (with defaults): `grid_size` [5,5], `max_moves` 25, `num_games` 6, `max_barriers` 5, `scoring.cop_win` 20, `scoring.thief_win` 10, `scoring.cop_loss` 5, `scoring.thief_loss` 5. | p.13 |
| HW-F26 | Submission = (a) public GitHub repo containing all source code + a scientific write-up named `README.md` at repo root; (b) README must be written in high academic-scientific language and include: formal Dec-POMDP tuple definition `⟨n, S, {Ai}, P, R, {Ωi}, O, γ⟩` mapped to this game; deep discussion of orchestration challenges (free-form NL coordination without rigid protocol, ambiguity handling, mutual-understanding strategies); visualization/proof of learning curves if RL was used, logs from the inter-group bonus MCP servers, CLI run evidence (Q-table/heuristic), GUI screen-capture simulation if a GUI was built. | p.13-14 |
| HW-F27 | Inter-group bonus competition: up to 10 bonus points on the final project. Pairing happens within 1 week of assignment publication. Each pair plays one full bidirectional game in the cloud: 6 sub-games total, split — first 3: Group A's Cop vs Group B's Thief; remaining 3: Group B's Cop vs Group A's Thief. Each group separately emails the **exact same** result via the Inter-Group Bonus JSON (full mutual agreement on data required). | p.14-15 |
| HW-F28 | Bonus point rules: (a) playing more than one other group is allowed and recommended; (b) highest cumulative bonus-game scorer in a pairing gets 10 pts, the loser gets 7 pts; an exact tie gives 5 pts to each; (c) final bonus score = average across all bonus pairings played; (d) mismatched/disagreeing reports between two groups → 0 bonus points for **both** sides for that pairing. | p.15 |
| HW-F29 | Recommended 8-stage development priority order: 1) grid rules/movement/barriers/capture logic; 2) basic MCP transport infra (2 independent servers, mutual reachability); 3) full local run via localhost; 4) decision-making mechanism (heuristic or Q-table); 5) NL protocol integration replacing rigid message exchange; 6) optional GUI visualizing agent/barrier movement in real time; 7) cloud deployment of MCP servers behind firewall/auth; 8) Gmail API integration, automated JSON report at end of 6 games. | p.16 |

## 2. HW PDF — Non-Functional / Architectural Constraints

| ID | Requirement |
|----|-------------|
| HW-N01 | Free natural language, no rigid protocol: agents are independent and decoupled; how each internally implements the NL exchange is irrelevant, as long as both understand each other. |
| HW-N02 | Client/Server separation: LLM lives in the client (orchestrator), MCP server only exposes tools — never the LLM. |
| HW-N03 | Gradual rollout: localhost (separate ports) → cloud (separate domains) → inter-group competition (with security: tokens, tunneling, firewall). |
| HW-N04 | 3 LLM-connectivity architectures available; hybrid (hold Ollama local, expose only the MCP server, outbound-only calls) is presented as the most secure for local dev. |
| HW-N05 | Security & automation: tokens (OAuth), ngrok Traffic Policy, no stored passwords, automated JSON reporting. |
| HW-N06 | Team & time-pressure management — explicitly named as a "unique skill" tied to the prisoner's-dilemma framing of the assignment (soft/process requirement, not a code requirement). |

## 3. HW PDF — Items needing confirmation

| ID | Open question | Why it matters |
|----|----------------|-----------------|
| HW-Q01 | **[Needs confirmation]** Exact LLM provider/model to use is not mandated by the PDF — it lists 3 architecture options and recommends public cloud API as simplest. We will default to architecture #1 (pluggable LLM client behind an interface) so the user can supply any provider key via `.env`, but the actual provider choice is the user's decision. |
| HW-Q02 | **[Needs confirmation]** Whether to implement the optional Q-Learning mechanism or a simpler heuristic for v1. The PDF explicitly states RL is optional; chunk plan treats Q-Learning as an enhancement chunk, not a blocking dependency. |
| HW-Q03 | **[Needs confirmation]** Whether a GUI (page 14, "if built") will be implemented — explicitly optional in the PDF ("graphs ... if visualization was performed"). Default plan: build a minimal CLI-only flow first; GUI is a stretch chunk. |
| HW-Q04 | **[Needs confirmation]** Cloud deployment target (Prefect Cloud mentioned only as an example, "for example") and exposure mechanism (ngrok/Localtonet/Nginx) are the user's choice — not graded as long as the 2-URL contract and security rules (HW-F17) are met. |
| HW-Q05 | **[Needs confirmation]** Gmail account / OAuth client credentials must be supplied by the user — cannot be fabricated. The target address `rmisegal+uoh26b@gmail.com` is fixed by the PDF and must not be changed. |
| HW-Q06 | **[Needs confirmation]** Inter-group bonus competition requires a second real student group; this cannot be executed inside this repository alone. The codebase must be *capable* of running it (two MCP URLs, bonus JSON schema) but actually playing it is an external, time-boxed (1 week from publication) activity the user must perform. |
| HW-Q07 | Starting positions: "random or chosen as strategy" (p.4) — implies start-position selection itself can be a strategic decision point exposed via config, not fixed. Default: configurable, random by default. |

---

## 4. Guidelines PDF — Mandatory Process & Structure Requirements

| ID | Requirement | Source (page) |
|----|-------------|----------------|
| SG-P01 | "Vibe coding" rule: full requirements + architecture must be defined and documented **before** any line of code is written. AI agents must follow PRDs/architecture docs, not improvise architecture mid-stream. | p.6 |
| SG-P02 | SDLC stages mandatory: (1) requirements doc (PRD) → (2) plan/architecture doc (PLAN, with TODO) → (3) TDD development → (4) validation/testing → (5) deployment/release docs → (6) maintenance/changelog. | p.5-6 |
| SG-D01 | Root `README.md` is **mandatory**, full user-manual level: install instructions, usage instructions (all modes/flags, CLI/GUI workflows), examples/screenshots, configuration guide, contribution guidelines, license & 3rd-party credits. | p.7 |
| SG-D02 | `docs/` folder is **mandatory** containing: `docs/PRD.md` (product requirements: overview, problem statement, target audience, goals/KPIs/acceptance criteria, functional + non-functional reqs, user stories, constraints, dependencies, out-of-scope, timeline), `docs/PLAN.md` (architecture: C4 model diagrams, UML, deployment diagrams, ADRs with rationale/trade-offs, API & data-model docs), `docs/TODO.md` (task list, phased, with Definition of Done per task and status: not-started/in-progress/done). | p.7-8 |
| SG-D03 | A dedicated `docs/PRD_<mechanism>.md` is required **for every significant algorithm or central mechanism** in the project (example names given: `PRD_ml_algorithm.md`, `PRD_authentication.md`, `PRD_search_engine.md`, `PRD_caching.md`). Each must cover: background/context, input/output specs, edge cases/limits/trade-offs and rationale, acceptance criteria & test approach. | p.8 |
| SG-D04 | Recommended canonical project layout (see `01_requirements_matrix.md` for the literal tree) — `src/<package>/` with `sdk/sdk.py`, `services/`, `shared/{gatekeeper.py, config.py, version.py}`, `constants.py`, `main.py`; `tests/{unit,integration}`; `docs/`; `config/{setup.json, rate_limits.json}`; `data/`; `results/`; `assets/`; `notebooks/`; root `README.md`, `pyproject.toml`, `uv.lock`, `.env-example`, `.gitignore`. | p.8-9 |
| SG-D05 | Mandatory work sequence: create+approve `PRD.md` → create `PLAN.md` → create `TODO.md` → create per-mechanism PRDs → get all docs approved **before** writing implementation code → begin dev, keeping `TODO.md` current → maintain results/visualizations and keep `README.md` updated throughout. | p.9 |

## 5. Guidelines PDF — Code & Architecture Requirements

| ID | Requirement | Source (page) |
|----|-------------|----------------|
| SG-C01 | Every code file capped at **150 logical lines** (blank/comment lines excluded). Over-limit files must be split via: extracting helper functions to a separate file, mixins, 50/50 split when a file mixes two concerns (read/write), moving magic values to `constants.py`, or splitting model definitions into their own file. | p.10 |
| SG-C02 | Code quality bar: docstrings explain *why*, not *what*; every public function/class/module documented; meaningful names; Single Responsibility + DRY enforced project-wide. | p.10 |
| SG-C03 | SDK architecture mandatory: the SDK is the single entry point for **all** business logic; CLI/GUI/REST layers contain **zero** business logic — they only call the SDK; external consumers can only reach the SDK, never internal modules directly. | p.11 |
| SG-C04 | OOP design with **zero tolerated code duplication**: forbidden patterns include the same function body in 2+ places, the same try/except pattern duplicated, the same identification/validation logic duplicated. Required fixes: extract shared mixin/base class, or use Template Method. Mixin rules: one concern per mixin, no overlapping method names between mixins, each mixin independently testable. | p.11-12 |
| SG-C05 | Central **API Gatekeeper** (singleton) must intercept **all** outbound external API calls: enforces rate limits before call, queues when limit is reached, retries on transient failure, logs every call. Required interface shown literally: `ApiGatekeeper.__init__(config: RateLimitConfig)`, `.execute(api_call, *args, **kwargs)`, `.get_queue_status() -> QueueStatus`. | p.13 |
| SG-C06 | Rate-limit configuration must be centralized in a JSON config (never hard-coded per call site); schema shown: `rate_limits.version`, `services.<name>.{requests_per_minute, requests_per_hour, concurrent_max, retry_after_seconds, max_retries}`. | p.13-14 |
| SG-C07 | Queue management on rate-limit breach: FIFO ordering, configurable max queue depth, backpressure alerts when queue is full, cleanup of stale queued requests when the rate window resets. | p.14 |
| SG-C08 | No magic values anywhere in source: literal URLs/rate limits/timeouts/secrets must be replaced with config lookups, named constants in `constants.py`, or `Enum`s. | p.17-18 |
| SG-C09 | Config architecture: a clear, versioned hierarchy under `config/` — `setup.json` (main app config), `rate_limits.json`, `logging_config.json`; secrets only via `.env` (git-ignored) with a committed `.env-example` containing placeholder values; never read secrets except via `os.environ.get(...)`. | p.18 |
| SG-C10 | Global semantic versioning starting at **1.00**, bumped on every meaningful change, tracked in 3 places: `src/<pkg>/shared/version.py`, the `"version"` key inside each JSON config, and `rate_limits.version`. | p.19 |
| SG-C11 | Package hygiene: package definition file (`pyproject.toml`) with name/version/author/license/deps; every package directory has `__init__.py` using `__all__` and `__version__`; only relative imports within a package, absolute outside; circular imports forbidden. | p.26 |
| SG-C12 | Parallelism guidance: multiprocessing for CPU-bound work, multithreading for I/O-bound work; thread safety via `queue.Queue`/context managers when used. | p.27 |
| SG-C13 | "Building block" component design: every component documents Input/Output/Setup data explicitly; enforces Single Responsibility, Separation of Concerns, and independent Testability (literal example class given: `DataProcessor`). | p.28-29 |
| SG-C14 | Recommended alignment with **ISO/IEC 25010** quality characteristics (functional suitability, performance efficiency, compatibility, usability, reliability, security, maintainability, portability) — used as a self-check, not a hard gate. | p.25 |

## 6. Guidelines PDF — Testing & Tooling Requirements

| ID | Requirement | Source (page) |
|----|-------------|----------------|
| SG-T01 | Strict TDD: Red → Green → Refactor. Tests must be written **before or alongside** implementation, never as an afterthought. | p.15 |
| SG-T02 | Every module has a matching test file; every public function/method has ≥1 dedicated test; tests must cover both the correct path and at least one error/edge path. | p.15 |
| SG-T03 | Test layout: `tests/unit/test_<module>/test_<file>.py` mirroring `src/` structure; `tests/integration/test_<feature>.py`; shared fixtures in `conftest.py`; mock all external dependencies (APIs, DB, filesystem where relevant); no test may depend on a live external service. | p.15 |
| SG-T04 | Global test coverage must be **≥85%**; build/CI must fail if coverage drops below this threshold. `pyproject.toml` coverage config given: `source=["src"]`, `omit=["src/main.py","*/tests/*","src/**/gui/*"]`, `fail_under=85`. | p.15-16 |
| SG-T05 | Edge cases must be explicitly identified and documented with description, expected behavior, and test reference; degradation must be graceful, with clear error messages and logging. | p.16 |
| SG-T06 | Test results must be reportable: automated test runs producing pass/fail rate reports, with logs of successful and failed runs retained. | p.16 |
| SG-T07 | **Ruff** linter must report **zero warnings**. `pyproject.toml` config given: `line-length=100`, `target-version="py310"`, `select=["E","F","W","I","N","UP","B","C4","SIM"]`, `ignore=["E501"]`. | p.17 |

## 7. Guidelines PDF — Dependency / Tooling / Versioning Requirements

| ID | Requirement | Source (page) |
|----|-------------|----------------|
| SG-U01 | **`uv` is the mandatory** package/venv manager. **`pip install`, `python -m venv`, `virtualenv` are forbidden.** Required command mapping: install deps → `uv sync` (not `pip install`); add dep → `uv add <pkg>` (not `pip install <pkg>`); run script → `uv run python script.py` (not `python script.py`); run tests → `uv run pytest tests/` (not `python -m pytest`); freeze/lock → `uv lock` (not `pip freeze`). | p.19-20 |
| SG-U02 | `pyproject.toml` is the **single source of truth** for dependencies — **no `requirements.txt`.** `uv.lock` must exist and be committed. No direct `pip`/`python -m`/script/CI calls outside `uv run`. | p.20 |
| SG-U03 | Git workflow: clear commit history with meaningful messages, feature branches for new functionality, PRs with code review before merge, tagging for releases. | p.19 |
| SG-U04 | A **Prompt Engineering Log** must be kept documenting all significant prompts used during AI-assisted development of the project: prompt text, context/goal, output received, iterations, lessons learned. | p.19 |

## 8. Guidelines PDF — Quick-Reference Gate Table (verbatim, p.33)

| Gate | Threshold | Verification method |
|------|-----------|----------------------|
| SDK architecture | All business logic via SDK | Code review |
| OOP / no duplication | ≤1 repeated pattern (2+ = violation) | Code review |
| API Gatekeeper | All external calls go through it | Code review + test |
| Rate limits | Centralized, never hard-coded | Config check |
| Pagination/queueing | — | Integration test |
| Version control | Starts at 1.00 | Module check |
| TDD | Red-Green-Refactor process followed | Process review |
| File size | ≤150 lines | Automated check |
| Linter | 0 warnings | `ruff check` |
| Test coverage | ≥85% | `pytest --cov` |
| Magic values | 0 in source | Code review |
| Secrets | `.env-example` present, 0 secrets in code | Automated scan |
| Dependency manager | Everything via `uv` | Automated check |

## 9a. Session-level project rules (not from either PDF, but binding)

These were issued directly by the user as explicit project constraints during the planning/skeleton session and are tracked with the same rigor as PDF-derived requirements (IDs `PROJ-R01`, `PROJ-R02` in `docs/01_requirements_matrix.md`):

| ID | Rule | Stricter than... | Enforcement |
|----|------|---------------------|--------------|
| PROJ-R01 | No Python file under `src/**/*.py`, `tests/**/*.py`, or `tools/**/*.py` may exceed **150 physical lines** (blank lines and comments counted). Refactor proactively once a file approaches ~120 lines. | SG-C01 (150 **logical** lines, blank/comments excluded) — PROJ-R01 is the stricter of the two, so satisfying it always satisfies SG-C01. | `tests/test_line_limits.py`, run as part of the standard test suite. Documented as ADR-006 in `docs/PLAN.md`. |
| PROJ-R02 | The project must contain **at least 510 PRDs**, organized as detailed PRDs in `docs/prds/` plus a numbered catalog in `docs/prds/catalog/PRD-0001.md..PRD-0NNN.md`, indexed by `docs/prds/PRD_INDEX.md`. | Not a PDF requirement at all — purely a session-issued documentation-depth requirement. | `tools/generate_prd_catalog.py` (tracked, ≤150 lines) regenerates the catalog deterministically from `tools/prd_catalog_data.json` (522 items as of this session, harvested from the requirements matrix, submission checklist, config files, and chunk plan — not randomly invented). |

## 9. Conflicts / Resolutions between the two PDFs

| Conflict | Resolution |
|----------|------------|
| HW PDF's example skeleton in the user's original task message includes `requirements.txt` and `pip`-era thinking | Guidelines PDF SG-U01/U02 explicitly forbids `requirements.txt` and `pip install` → we use `pyproject.toml` + `uv.lock` exclusively, dropping `requirements.txt`. |
| User's suggested skeleton has a flat `src/hw6_race/` package with `controller.py`, `agents/`, `mcp/`, `race/`, `logging_utils/`, `utils/` | Guidelines PDF SG-D04/SG-C03 mandates an `sdk/` entry-point layer plus `shared/{gatekeeper.py, config.py, version.py}` and `services/`. We merge both: keep the HW-domain subpackages (`agents/`, `mcp/`, `race/`) as **services**, add the mandatory `sdk/`, `shared/`, `constants.py` layer on top so CLI/tests only ever call the SDK. |
| User's suggested `docs/prds/PRD-00X-*.md` naming vs. Guidelines PDF's `docs/PRD_<mechanism>.md` naming | Both are kept: `docs/PRD.md`, `docs/PLAN.md`, `docs/TODO.md` satisfy the mandatory guideline docs; `docs/PRD_q_learning.md` satisfies SG-D03 for the central decision-making algorithm; `docs/prds/PRD-00X-*.md` are kept as the user explicitly requested them as supplementary chunk-level PRDs (not a guideline requirement, but not in conflict with one either). |

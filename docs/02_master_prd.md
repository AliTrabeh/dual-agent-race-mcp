# 02 — Master PRD (Index)

The canonical, guideline-mandated PRD is `docs/PRD.md` (required filename per Guidelines PDF SG-D02 — must be exactly `docs/PRD.md`, not renumbered). This file exists only as the numbered-index pointer the user's requested doc set expects, and to record the relationship between the various requirement/PRD documents so nothing is duplicated inconsistently.

## Document map

| Document | Role | Mandated by |
|----------|------|--------------|
| `docs/PRD.md` | Canonical product requirements (overview, goals, functional/non-functional reqs, user stories, constraints, timeline) | Guidelines SG-D02 (exact filename) |
| `docs/PLAN.md` | Architecture: C4 diagrams, deployment diagram, ADRs, API/data notes | Guidelines SG-D02 (exact filename) |
| `docs/TODO.md` | Phased task list with Definition of Done | Guidelines SG-D02 (exact filename) |
| `docs/PRD_q_learning.md` | Per-mechanism PRD for the optional Q-Learning decision strategy | Guidelines SG-D03 |
| `docs/prds/PRD-001..007-*.md` | Chunk-level supplementary PRDs (purpose/scope/inputs-outputs/acceptance/edge cases/testing/risks/DoD per implementation area) | User's explicit request in this session — not a guideline requirement but compatible with one |
| `docs/00_source_analysis.md` | Raw requirement extraction from both PDFs | This session's Phase 0 |
| `docs/01_requirements_matrix.md` | Traceability matrix, requirement → artifact → chunk → status | This session's Phase 0 |
| `docs/03_architecture.md` | Narrative architecture discussion (deeper prose than PLAN.md's structured artifacts) | This session's Phase 1 |
| `docs/04_implementation_chunks.md` | Chunk-by-chunk implementation plan (0–11) | This session's Phase 2 |
| `docs/05_testing_strategy.md` | TDD approach, coverage gate, staged sanity-check plan | This session's Phase 1 |
| `docs/06_submission_checklist.md` | Final pre-submission checklist merging both PDFs' checklists | This session's Phase 1 |
| `docs/07_risks_and_open_questions.md` | All `[Needs confirmation]` items + technical risks | This session's Phase 1 |
| `docs/08_claude_work_log.md` | Prompt Engineering Log (SG-U04) + decision log | This session's Phase 1, kept current throughout |

No content should be duplicated verbatim across these files beyond short cross-references — each has a single owning concern. If a future edit changes a requirement, update `docs/00_source_analysis.md` first, then propagate via the matrix.

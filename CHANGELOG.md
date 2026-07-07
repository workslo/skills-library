# Changelog

All notable changes to the Skills Library. Newest first. Dates are YYYY-MM-DD.

## [Unreleased]

### Added
- Memory: created `memory/resolved-flags.md` to record investigated and closed
  security/monitoring flags. First entry: GitGuardian Bearer Token in the
  `generative-ai` repo (resolved 2026-06-27, non-issue — forked external repo,
  never live, never Shane's code). Future diff runs should check this file
  before surfacing a flag as active.
- Content: adapted the three harvested writing skills into on-domain tax-ops
  entries (SLO-105). `client-communication-drafter` (from copywriting),
  `desk-kb-content-planner` (from content-strategy), and
  `iterative-tax-memo-writer` (from deep-write) are `communicate`-stage skills
  that pass validation; the catalog now builds 23 entries. Added
  `content/harvest/README.md` to make the build's harvest exclusion explicit and
  record the source-to-entry mapping.
- Docs: added `docs/retrieval-guidance.md` (SLO-102, SLO-109), verifying the
  M365 Copilot and SharePoint-agent grounding claims against current Microsoft
  documentation with citations. Four of five claims confirmed; the "restate
  tables as bullets" advice is not documented by Microsoft and is flagged as an
  internal heuristic, not vendor guidance.

### Changed
- Agent contract accuracy: corrected the entry count in `AGENTS.md`/`CLAUDE.md`
  from a stale "14 today" to the actual 23 (validator-confirmed), and named the
  six meta entries plus the three writing-support entries the prose had omitted.
  Added a "Harvest sources" section documenting `agent-skills/` (a read-only
  clone of `addyosmani/agent-skills`) as a decomposition spec, and gitignored it
  so the nested clone is not half-tracked.
- Agent contracts: reconciled `CLAUDE.md` and `AGENTS.md` to the dual-agent
  reality. Both files claimed their own tool was the settled, sole agent;
  Codex harvests content while Claude Code owns the build, scaffold, and
  frontend, sharing `.claude/skills/` and `memory/`. `CLAUDE.md` is now the
  canonical contract; `AGENTS.md` is the Codex-facing companion and is tracked
  (removed from `.gitignore`). Fixed the broken `.Codex/skills/` pointer in
  `AGENTS.md` to the real shared `.claude/skills/` path.
- Content harvest: moved the generic writing-skill candidates (`content-strategy`,
  `copywriting`, `deep-write`) out of the live `content/entries/` build source
  and into `content/harvest/writing-skills/` with a recommendation note for
  later tax-ops adaptation. This preserves the source packs while keeping the
  flat YAML catalog clear.
- Domain taxonomy: mirrored the GL Reconciler cause-taxonomy expansion into the
  plugin shared domain skill and the exported GL Reconciler skill metadata, so
  the legacy catalog and plugin marketplace stay aligned.

### Fixed
- Domain reference: corrected two IRS mappings in `.claude/skills/tax-ops-domain.md`
  and the mirrored `plugins/tax-ops-shared/skills/tax-ops-domain/SKILL.md`,
  verified 2026-06-18 against current IRS instructions. Substitute payments in
  lieu of dividends move from "other income" to 1099-MISC Box 8 (Instructions
  for Forms 1099-MISC and 1099-NEC, Rev. 04/2025). 1042-S "other income"
  corrected from code 51 to code 23; code 51 is interest on certain actively
  traded or publicly offered securities (2026 Instructions for Form 1042-S).
- Validation: remediation detection in workflows now scans each step's `output`,
  not just `title` and `prompt`. A remediation described only in the output no
  longer slips past the human-sign-off-gate rule. (`build/build.py`)
- Validation: a YAML-quoted `tier` (for example `"2"`) is accepted instead of
  hard-failing. The validator now coerces with `int()`, matching the renderer.
- Validation: the tool-agnostic scan on `core_function` catches plural tokens.
  "calls external APIs" now trips the rule, where only "API" did before.
- Offline check: patterns catch protocol-relative references (`//cdn…`), not just
  `https?:`. A protocol-relative external src, href, or `url()` is now flagged.
- `.gitignore`: secret coverage widened to `.env*`, `credentials.json`,
  `token.json`, `oauth_creds.json`, `client_secret*.json`, `.ssh/`, `.mcp-auth/`.
- Memory layer: hardcoded absolute paths made portable. The repo-review agent's
  persistent-memory section dropped `/Users/shaneslo/...agent-memory/...` and now
  defers to the `memory: project` managed store, created on first write, removing
  the false "this directory already exists" claim. `memory/projects/skills-library.md`
  no longer pins the repo to an absolute path.

### Added
- Track A card polish (issue #18): desktop cards are square (`aspect-ratio:1/1`) and
  render three per row at 1280px via a `min-width:1024px` grid; mobile keeps the
  single-column, content-height fallback (`aspect-ratio:auto`). A new
  `stage_count(entries)` helper drives the `<!--STAGE_COUNT-->` hero substitution
  off stages actually present in the content instead of the hardcoded schema count.
  Copy buttons carry `aria-live="polite"` so the "Copied" status is announced.
  Tests: a `stage_count` unit test plus offline regression cases for external `src`
  and `@import` in the page chrome. (`build/build.py`, `build/template.html`,
  `tests/test_validate.py`)
- `build/serve.py`: builds the catalog then serves `dist/` over HTTP for local
  review (`python build/serve.py`, `--port`, `--no-build`). Convenience only; the
  page still loads nothing external.
- `build/screenshot.mjs` and `docs/screenshots/`: Playwright capture of the
  rendered catalog (top, full page, and an open entry dialog) for review without
  running the build. Uses the environment's cached chromium via `CHROME_BIN` or
  the default Playwright path.
- `docs/project-state.md`: a 2026-06-14 snapshot reconciling what the repo holds
  against what CLAUDE.md and the dossier claim. Flags the 14-to-20 entry drift, the
  coexisting YAML and plugin-marketplace layouts, four top-level directories CLAUDE.md
  omits, two content entries with no plugin home, and the helper-command
  classification clash between `docs/authoring-plugins.md` and the `claude-*-command`
  catalog entries. Recommendations only; no source files changed.
- Build methodology recorded as a standing rule: thin vertical slice first. Prove
  one skill all the way up (author, `/validate`, `/build`, render check on
  `dist/skills-library.html`) before widening the library. Short form in CLAUDE.md,
  full rationale in `memory/projects/skills-library.md`.
- Interim bookkeeping rule in CLAUDE.md ("Keep the productivity suite current"):
  when code, a document, or the environment changes, TASKS.md and CHANGELOG.md move
  in the same pass, before push. Stands in until a mechanism is chosen.
- `mocks/skills-library-linear.html`: standalone Linear-style interface mock
  (PR #24, merged 06-06). Backfilled here; it landed without a changelog entry.
- `content/entries/period-close-reconciliation-workflow.yaml`: a period-close
  tie-out runbook. It chains existing single-task assets (data-quality profiler,
  GL reconciler break triage, metric-movement diagnostics, KPI readout) into one
  ordered close, with a filing-readiness step and four human sign-off gates. Sits
  in the `research` stage beside the break-diagnostic workflow without overlapping
  it: this one reconciles a whole period, that one diagnoses a single break.
- `tests/test_validate.py`: contract tests for `validate_entries`, one per rule,
  with regression cases for each fix above. Run with `python -m pytest`.
- `requirements-dev.txt` and `requirements.txt` to pin the build and test deps.
- Tracked `.claude/agents/repo-review-orchestrator.md` (was untracked).
- `memory/README.md`: defines the memory layer, its boundary with the build
  (`build/build.py` reads only `content/entries/`, never `memory/`), the
  hot-cache/cold-store context model, the per-file roles, the `projects/`
  convention, and how agent memory under `.claude/` differs. CLAUDE.md "Where
  things live" and the build-pipeline skill now point at the layer, and a comment
  at `CONTENT_DIR` in `build/build.py` records that memory never compiles.

### Decided (resolves the three 2026-05-31 design calls)
- Workflow stage handling: resolved on `main` by PR #9, which made `stage` a
  required field for every entry and added a Type-axis filter carrying a
  "Workflows" control (`data-type="workflow"`). That surfaces all workflow
  assets regardless of stage and removes the orphaned `data-stage="workflow"`
  value the review flagged. No template change ships in this changelog entry.
- Spec criterion 8 no longer ties `tier` to an uncommitted "research inventory".
  Tier is an integer 1 to 4 set from source provenance, with the rationale
  carried in each entry's `source` and `maturity` fields. The deep-research
  inventory is a research-phase artifact, not a build input. (`SKILLS_LIBRARY_SPEC.md`)
- Exemplar terminal form: bracketed `[INSERT: …]` placeholders are the intended
  terminal state for `adapt` and `author-from-spec` entries, not an incomplete
  one. They mark the adaptation surface where firm-specific domain knowledge is
  supplied at use time. The spec's acceptance criteria now state this, so open
  inserts pass rather than read as unfinished. (`SKILLS_LIBRARY_SPEC.md`)

## [0.1.0] - 2026-05-31

### Added
- Initial scaffold: build pipeline, offline HTML template, spec, domain skills.
- First exemplar entry: `gl-reconciler-break-triage`.

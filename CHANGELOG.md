# Changelog

All notable changes to the Skills Library. Newest first. Dates are YYYY-MM-DD.

## [Unreleased]

### Changed
- Agent contract accuracy: corrected the entry count in `AGENTS.md`/`CLAUDE.md`
  from a stale "14 today" to the actual 20 (validator-confirmed), and named the
  six meta entries the prose had omitted (the two knowledge entries, the three
  `claude-*-command` entries, and `period-close-reconciliation-workflow`). Added
  a "Harvest sources" section documenting `agent-skills/` (a read-only clone of
  `addyosmani/agent-skills`) as a decomposition spec, and gitignored it so the
  nested clone is not half-tracked.
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

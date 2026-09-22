# Changelog

All notable changes to the Skills Library. Newest first. Dates are YYYY-MM-DD.

## [Unreleased]

### Changed
- Content: widened the `business-process-analysis-workflow` drafting steps to
  full writer depth. The three condensed prompts now carry the complete W1 to
  W7 rendering rules from the preserved spec: the four-subsection components
  format with placeholder paths and the dominant-category tool heading, the
  two step renders with hierarchical versus role-grouped branching and
  explicit decision-point and loop formats, the two role renders with
  named-individual attribution and unresolved-entity handling, the fixed
  pattern taxonomy with its table format, and the percentile banding versus
  day-count rules for the time estimate. W8 and W9 already ride at full depth
  in `process-improvement-fit-assessor`. The harvest README now points to the
  spec file as provenance rather than a pending widening pass. Review on the
  widening PR caught adaptation drift from the preserved spec; aligned in the
  same PR: the outlier band renders only when the sheet records a maximum,
  anchored at that value; the pattern taxonomy uses the spec's exact category
  labels; the unknown-path placeholder names the specific system; the tool
  subsection heading follows the explicit category mapping; the time-estimate
  close names cycles and third-party dependencies that extend a case past the
  bands.

### Added
- Plugin: added `plugins/m365-copilot-skills/` with a `create-a-skill`
  authoring skill that interviews users and drafts installable `SKILL.md`
  files for Word, Excel, PowerPoint, Copilot Cowork, and AI in SharePoint.
  Added host-neutral and host-specific references under
  `skills/create-a-skill/references/`, deployable declarative-agent and
  SharePoint assets under `skills/create-a-skill/assets/`, and registered the
  plugin in `.claude-plugin/marketplace.json`.
- Content: harvested the desk's BPA generator orchestration spec into a
  process-analysis set (#22). `procedure-fact-normalizer` turns any procedure
  document into a verified fact sheet, `process-improvement-fit-assessor`
  renders approved-catalog improvement opportunities plus an explicit
  generative-assistance fit call, and `business-process-analysis-workflow`
  chains gate, normalization, drafting, and assembly with three sign-off
  gates. The parallel writer fan-out becomes sequential prompts over one
  verified fact sheet, since an analyst runs one conversation at a time. The
  cleaned source spec is preserved under `content/harvest/bpa-generator/`
  with the full nine writer prompts; the catalog builds 26 entries.
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
- Spec: completed the evaluator review of `SKILLS_LIBRARY_SPEC.md` (2026-08-04),
  open since 2026-05-31. All ten acceptance criteria pass against the as-built
  23-entry library. Findings incorporated in place: the one-YAML-file-per-entry
  format decision (sections 2, 9, 11), the automated validation scope (sections
  4, 5, 7), the exemplar's filled cause taxonomy (section 8), the shipped
  navigation with the Type filter and prompt-text search (section 6), all four
  section 11 open questions closed, a v1-shipped roadmap note (section 12), and
  a new section 13 review record. Status moved from "Draft for review" to
  reviewed.
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
- Validation: the `stage` allowed-value check now runs for every entry type.
  It sat in the asset-only branch, so a workflow with an unknown stage passed
  `--check` and then dropped out of the rendered stage groups silently. Found
  by review on PR #39 during the spec-review pass. New contract tests cover
  the stage enum for assets and workflows and the adaptation enum.
  (`build/build.py`, `tests/test_validate.py`)
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
- `.gitignore`: `node_modules/` and npm manifests are ignored. The playwright
  package that `build/screenshot.mjs` imports is installed ad hoc for a render
  check and is not part of the build; the install left an untracked tree.
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

# AGENTS.md

Guidance for Codex (and any non-Claude agent) in this repo. The project files are the source of truth. Read them before acting.

## Dual-agent repo
Two agents work here, and the split is deliberate. It is not a migration in progress.
- Codex harvests and adapts content. Most `content/entries/*.yaml` were decomposed from first-party OpenAI plugin skills and re-expressed as tool-agnostic prose.
- Claude Code owns the build pipeline, scaffolding, tests, and frontend.

Both share the same domain skills under `.claude/skills/` and the same `memory/` cold store. Neither tool is the sole agent. Do not strip the other's work.

This file is the canonical, fuller contract for every agent (Claude Code reads it via the `CLAUDE.md` symlink). The Codex-specific deltas are below; the full contract merged from the former `CLAUDE.md` follows further down.

## What this repo is
A copy-and-adapt library of AI assets (prompts, skills, agents, workflows) for Goldman Sachs prime brokerage tax-reporting operations. Content is tool-agnostic and compiles to one offline HTML file. The execution layer can change without rewriting content.

## Core principle
The question is never which tools we have, but what exists that works. Three tests for any asset: understand it, decompose it to its core function and rebuild it, adapt it to the domain now. Treat credible repos as specifications, not software: harvest the decomposition, drop code that will not run, re-express the rest as prompts the available assistant runs. The edge is the domain knowledge poured into the gap the repo cannot fill.

## Harvest sources
Credible upstream repos live locally as read-only specifications to decompose, not code to run or vendor. They are gitignored and never compile into `dist/`.
- `agent-skills/`: a clone of `github.com/addyosmani/agent-skills`, a lifecycle of engineering skills (`/spec`, `/plan`, `/build`, `/test`, `/review`, `/ship`). Harvest its decomposition, adapt to the tax-ops domain, do not import it wholesale.

## Where Codex things live
- `.claude/skills/tax-ops-domain.md` — break taxonomy, routing rules, tax-form mappings, the three-test framework. Shared, not Claude-only. Load it when authoring or adapting an entry. (This pointer previously read `.Codex/skills/`, a path that never existed; the skills live under `.claude/skills/`.)
- `.claude/skills/build-pipeline.md` — the content-layer model, the build steps, the acceptance criteria.
- `.codex/` — Codex local scaffolding (agent and environment). Gitignored, not part of the build. `.codex/agents/repo-review-orchestrator.toml` mirrors `.claude/agents/repo-review-orchestrator.md`; keep the two in step if you change one.

## Build commands
Same as in `CLAUDE.md`. The script is the source of truth.
- `python build/build.py --check` — validate every entry against the schema and the hard rules. No build.
- `python build/build.py` — validate, compile, run the offline check, write `dist/skills-library.html`.
- `python -m pytest` — run the validator contract tests. Install deps first with `pip install -r requirements-dev.txt`.

## Keep the bookkeeping current
Whenever you change code, a document, or the environment, update `TASKS.md` and add a line to `CHANGELOG.md` under `[Unreleased]` in the same pass, before push. A doc-only or environment-only change still earns a changelog line.

## Writing preferences
BLUF. Specific over general, decisive. No em dashes. Avoid "not X but Y" constructions. Sentence-case headings. Vary sentence length. End on a fact or a next step, not a summary.

Banned vocabulary: leverage, utilize, robust, seamless, streamline, empower, foster, paradigm, landscape, journey, pivotal, cutting-edge, holistic, demonstrate, facilitate, ensure, endeavor, game-changer, state-of-the-art.

Banned transitions: Moreover, Furthermore, Additionally, Notably, Importantly, It is worth noting that.

Banned constructions: the single-caveat reveal, where one item gets teed up as specially significant. No "one X remains, and it's the Y", no "this one's load-bearing", no "the load-bearing X". Drop the faux-candor framing. State the point plainly. The word "load-bearing" as a descriptor is banned.

Honor these in every non-code string: skill bodies, domain-gap notes, comments, prompt text, setup instructions. Code is exempt.

---

## Full contract (merged from former CLAUDE.md)

The sections below were the canonical fuller contract that previously lived in `CLAUDE.md`. `CLAUDE.md` is now a symlink to this file; the content is preserved here verbatim. That preserved historical section is reference material; new edits still follow the writing preferences above.

### Me
Finance operations on GS prime brokerage client tax reporting.

### Workflow spine
1. Receive issues by email or workflow that need research.
2. Open the client account and the back-office transaction log, review it.
3. Decide whether a manual update is needed and how: UI, XML, SQL, or plugin.
4. Communicate status to the field and to leadership.
5. Analyze internal KB articles, client statements, and tax documents.

### Domain weighting
Reconciliation, exception research and handling, cost-basis and transaction analysis, tax and regulatory reporting, trade support, issue classification and routing.

### Build methodology: thin vertical slice first
Prove one asset all the way up before going wide. From the first five minutes, take a single skill through the whole stack: author the entry, run `/validate`, run `/build`, then open `dist/skills-library.html` and confirm it renders and presents well. A working slice of one beats a broad pack that has never compiled. Widen only after the slice holds, adding entries and rebuilding with a render check each pass. A change that spans the stack (schema, build, or template) rides through one entry end to end before it touches the rest. Full rationale in `memory/projects/skills-library.md`.

### Domain terminology
Break: a reconciliation discrepancy to research and resolve. Tie-out: reconcile a statement against an authoritative source. Cost basis: original asset value for tax gain and loss. Remediation path: UI, XML, SQL, or plugin. 1099-DIV/B/INT, 1042-S, FATCA, CRS: the reporting forms and regimes. Full definitions live in `memory/glossary.md`. Full break taxonomy, routing rules, and tax-form mappings live in the domain skill below.

### Where things live
- `content/entries/*.yaml` — one asset per file, 23 today. Two domain packs plus a handful of meta entries. A Data Analytics pack covers metric-movement diagnostics, data-quality profiling, the break-backlog KPI readout, the dashboard brief, the report writer, and an end-to-end diagnostic workflow. A Gainskeeper operations pack covers exception research, gain/loss tie-out, email intake triage, field-status replies, KB review, the break tracker, and work-item routing. A writing-support set covers client communication, desk KB content planning, and iterative tax memo drafting. The rest document the library itself: the `tax-ops-domain-knowledge` and `build-pipeline-knowledge` reference entries, the three `claude-*-command` build-command entries, and the `period-close-reconciliation-workflow`. `gl-reconciler-break-triage.yaml` is the exemplar every entry matches for shape and depth. Schema in `SKILLS_LIBRARY_SPEC.md` section 4 (assets) and section 5 (workflows).
- `build/build.py` — validates content, renders each entry, runs the offline check, compiles the HTML. The build reads `content/entries/` and nothing else.
- `build/template.html` — the offline shell. Inlined CSS and JS, no external dependencies. The build injects entries at the `<!--ENTRIES-->` marker.
- `dist/skills-library.html` — generated output, gitignored. Do not hand-edit; the next build overwrites it.
- `tests/test_validate.py` — pytest contract tests, one per validation rule, with a regression case behind each past fix. Run `python -m pytest`.
- `requirements.txt` (pyyaml, markdown) and `requirements-dev.txt` (adds pytest) — the pinned dependencies.
- `.claude/skills/tax-ops-domain.md` — break taxonomy, routing rules, tax-form mappings, three-test framework. Load it when authoring or adapting an entry.
- `.claude/skills/build-pipeline.md` — the content-layer model, the build steps, the ten acceptance criteria.
- `.claude/commands/*.md` — the `/validate`, `/build`, and `/new-entry` slash commands.
- `.claude/agents/repo-review-orchestrator.md` — the multi-angle review agent. It keeps its own `memory: project` store under `.claude/`, owned by the agent and separate from the operator memory layer below.
- `SKILLS_LIBRARY_SPEC.md` — the contract. Section 8 is the quality bar, section 10 the acceptance criteria.
- `CHANGELOG.md` — what changed, newest first. `TASKS.md` — active work, waiting-on items, someday, and done.
- `memory/` — operator context, the cold store this file defers to. `memory/README.md` defines the layer and its boundary with the build. `memory/glossary.md` holds full term definitions, `memory/company.md` the environment, `memory/projects/skills-library.md` this repo's dossier. None of it compiles into `dist/`.

### Build commands (slash-command forms)
The slash commands wrap the script. The script is the source of truth, so either form works.
- `/validate` or `python build/build.py --check` — check every entry against the schema and the hard rules. No build. A non-zero exit names the file, the field, and the rule.
- `/build` or `python build/build.py` — validate, compile, run the offline check, write `dist/skills-library.html`. A failed offline check aborts before any file is written.
- `/new-entry <slug> "<name>"` — scaffold a content entry with every schema field pre-filled.
- `python -m pytest` — run the validator contract tests. Install deps first with `pip install -r requirements-dev.txt`.

### Adding or changing an entry
1. Scaffold with `/new-entry`, or copy the exemplar.
2. Write a tool-agnostic body. Put firm specifics in bracketed `[INSERT: …]` placeholders and pull the real content from `.claude/skills/tax-ops-domain.md`. Open inserts are the intended terminal form for `adapt` and `author-from-spec` entries, not an unfinished state.
3. Write a substantive `domain_gap` to the section 8 standard: name what the analyst supplies and what changes once it is filled. A one-line gap fails.
4. Run `/validate`, clear every failure, then `/build`.
5. Match the exemplar. An entry that cannot pass the three tests visibly is not ready.

### What validation enforces
- Every required field is present for the entry type. Assets carry the section 4 fields, workflows the section 5 fields.
- `id` is a stable slug that matches the filename stem and is unique across the library.
- `tier` is an integer 1 to 4. `stage`, `type`, and `adaptation` hold allowed values only.
- `core_function` names no tool. A match on sql, xml, plugin, database, connector, runtime, sdk, mcp, api, rest, graphql, endpoint, or cron fails the entry, since the core has not been decomposed.
- `domain_gap` is present and substantive for every asset.
- A workflow carries at least one explicit human-sign-off gate, and any workflow with a remediation step must gate it.
- The compiled HTML loads nothing external and uses no browser storage. The offline scan catches external `src` and `href`, `<link>`, external `<script src>`, `@import`, remote `url()`, and any `localStorage`, `sessionStorage`, `indexedDB`, or cookie use in the page chrome.

# Skills Library — Build Specification

**For:** Build contract and quality bar for the Skills Library
**Author:** Tax-Ops AI working group
**Date:** 2026-05-31
**Reviewed:** 2026-08-04, evaluator pass against the as-built library. All ten acceptance criteria pass. Findings incorporated in place; record in section 13.
**Status:** Reviewed, current

---

## 1. Bottom line

Build a single, self-contained, offline HTML file that presents a curated set of AI assets (prompts, skills, agents, workflows) for prime brokerage tax-reporting operations. Each asset sits in an expandable block with a one-click copy button, so a user can lift the raw prompt or skill text and paste it into whatever assistant they have. Authoring of the full asset bodies happens in the build chat, not in this spec. This spec defines the data model, the organization, the build pipeline, the offline constraints, and the quality bar, and it includes one fully worked exemplar so the evaluator can judge what "good" looks like before forty more are written.

The governing principle for every entry: the question is never which tools we have, but what exists that works. Each asset is captured as tool-agnostic content (the decomposed core function plus the domain knowledge poured into it), so the same library survives a change of execution layer. When Claude or an internal Goldman tool lands, the content does not get rewritten; only the execution notes get upgraded.

---

## 2. The token strategy (the part to get right first)

The naive build hand-writes one giant HTML file with forty-plus expandable blocks, each carrying inline content, styling, and script. That approach is expensive and fragile: every revision re-emits the whole file, the model spends most of its output budget on repetitive markup rather than on the prompt text that carries the value, and a one-line fix to a single skill risks corrupting the surrounding HTML.

The build instead separates content from presentation and assembles the file programmatically.

| Layer | What it holds | Format | Who writes it |
|---|---|---|---|
| Content | The actual asset bodies, metadata, domain-gap notes | One YAML file per entry in `content/entries/` (decided at build; section 11) | Authored once per asset, edited in place |
| Template | The HTML shell: head, inlined CSS, the expandable-block component, the copy-button script | HTML, written once | Built once, reused |
| Build | A short Python script that reads the content, loops over entries, and injects each into the template | Python | Written once, re-run on every change |

The payoff is direct. Output tokens are spent on content, which is the asset, rather than on boilerplate, which a loop generates for free. Adding or editing a skill means editing a small content block and re-running the script; the model never re-emits the full HTML. The evaluator and any reviewer can read the content in plain Markdown without wading through markup. And the same content layer can later be re-skinned or re-exported for a different tool without touching a single prompt.

This is the same logic we apply to the source repos: harvest the structure, express it in the cheapest durable form, generate the presentation last. This spec is delivered as Markdown for exactly that reason. A draft-stage review document does not earn the HTML tax; the interactive HTML is reserved for the final library a user actually opens.

---

## 3. Where the full prompts get written

Decision: the schema and one worked exemplar live in this spec. The remaining asset bodies are authored in the build chat, against the schema and the exemplar.

Rationale. The evaluator needs to assess the plan and the quality bar, which one complete exemplar establishes. Forty full prompts would bury the plan and make the spec unreviewable in one sitting. Authoring is the expensive step, and it belongs in the build phase where the content layer (section 2) keeps it cheap and editable. The exemplar in section 8 is the contract: every other entry matches its shape and depth.

---

## 4. Asset entry schema

Every non-workflow asset carries these fields. Required unless marked optional.

| Field | Purpose |
|---|---|
| `id` | Stable slug, e.g. `gl-reconciler-break-triage` |
| `name` | Human-readable title |
| `type` | One of: prompt, skill, agent, workflow |
| `stage` | Workflow stage: intake-classify, research, remediate, communicate |
| `tier` | Credibility tier 1 to 4, set from source provenance: first-party standing, fork and star count, and release recency, all captured in the entry's `source` and `maturity` fields |
| `source` | Origin name plus link |
| `core_function` | One sentence: the decomposed core, stripped of tooling (test 2) |
| `domain_fit` | Which domain priority it serves and how directly |
| `adaptation` | One of: use-as-is, adapt, author-from-spec |
| `body` | The copy-pasteable asset text. This is the expandable payload |
| `domain_gap` | What domain knowledge the user must supply to make it role-fit (test 3). Never blank for a finance asset |
| `maturity` | Maintenance or reputation signal: stars, vendor backing, last-updated, author standing |
| `notes` | Optional: caveats, licensing, prerequisites |

Two rules the evaluator should enforce. First, `core_function` must be tool-agnostic; if it names a database, a language runtime, or a connector, it has not been decomposed. Second, `domain_gap` must be substantive for every finance asset, because no asset in the inventory is tax-aware out of the box, and an entry that pretends otherwise is a defect.

As built, `python build/build.py --check` enforces both rules mechanically, plus the structural ones: `id` matches the filename stem and is unique across the library, `tier` is an integer 1 to 4, and `stage`, `type`, and `adaptation` hold allowed values only. The tool scan on `core_function` fails a match on sql, xml, plugin, database, connector, runtime, sdk, mcp, api, rest, graphql, endpoint, or cron, plurals included. Each rule carries a contract test in `tests/test_validate.py`.

---

## 5. Workflow card model

A workflow is an ordered sequence of skills plus connective logic and decision gates, so it renders as a distinct card type rather than a single copy block. Fields:

| Field | Purpose |
|---|---|
| `id`, `name`, `tier`, `source`, `domain_fit`, `maturity` | As above |
| `trigger` | What starts the workflow (an inbound issue, a period close, a flagged break) |
| `steps` | Ordered list. Each step: a title, an optional reference to an asset `id`, an inline prompt, and an `output` |
| `gates` | Explicit human-sign-off points. A workflow with no sign-off gate on a remediation step is a defect |
| `output` | The end artifact (a break table, a status note, a corrected log) |

Rendering: a numbered sequence, each step expandable to reveal its prompt, with sign-off gates marked inline and visually distinct. The user can copy a single step's prompt or the whole sequence.

The validator enforces the gate rule: every workflow carries at least one explicit sign-off gate, and remediation detection scans each step's title, prompt, and output, so a remediation described only in a step's output cannot slip past ungated.

---

## 6. Organization and navigation

Primary grouping is by workflow stage, because that matches the moment of use: intake-classify, research, remediate, communicate. Credibility tier appears as a tag on each card, preserving the trust signal from the inventory without making it the navigation axis. A user pulling an asset mid-task thinks in terms of the stage they are in, not the tier of the source.

Each card shows, collapsed: name, type, stage, tier tag, core function, adaptation status. Expanded: the body, the domain-gap note, source, and maturity. Top-of-file controls: filter by stage, filter by type, filter by tier, and a text search across names, core functions, and prompt text.

As built: entries render in stage sections, the expanded view is an accessible dialog, and workflows surface through the Type filter rather than a synthetic stage (the 2026-06-03 design call). The search index covers prompt bodies, which goes past the original names-and-core-functions plan and stays.

---

## 7. Offline and self-contained requirements

1. The final file runs from `file://` with no network. All CSS and JavaScript are inlined. No external CDN, font, or script dependencies, because any of them breaks the offline promise the moment the user is on a locked-down machine.
2. The copy button writes clean plain text to the clipboard: the raw prompt only, with no HTML entities, no surrounding markup, and no smart-quote substitution that would corrupt a pasted prompt.
3. No browser storage APIs. The file is read-only reference; it holds no user state.
4. The file degrades gracefully if the clipboard API is unavailable, by selecting the text for manual copy.

All four hold in the shipped artifact, and the offline promise is checked on every build: the scan fails the compiled page on external `src` or `href`, `<link>`, external `<script src>`, `@import`, remote or protocol-relative `url()`, and any browser-storage or cookie use in the page chrome. The copy path degrades in order: clipboard API, then legacy execCommand, then select-for-manual-copy, with the result announced for screen readers.

---

## 8. Worked exemplar (the quality bar)

This is one complete entry. Every other entry matches this shape and depth.

```yaml
id: gl-reconciler-break-triage
name: Transaction-Log Break Triage (GL Reconciler, decomposed)
type: skill
stage: research
tier: 1
source: anthropics/financial-services — GL Reconciler agent (Apache 2.0)
core_function: >
  Compare two records of the same activity, surface every discrepancy,
  classify each by likely cause, and stage the judgment calls for a human.
domain_fit: >
  Priority 1, directly. The core of exception research: turning a raw
  transaction log into a triaged break list a human can act on.
adaptation: author-from-spec
maturity: >
  First-party Anthropic, repo at ~29k stars / 4.1k forks, released
  2026-05-05. Source agent assumes connectors and a runtime we do not
  have; this is the decomposed, prompt-only re-expression.
```

**body** (the copy-pasteable skill text):

> You are assisting a prime brokerage tax-operations analyst. You will receive two files: a client back-office transaction log, and a reference source for the same period. Work in three passes and show your work at each pass.
>
> Pass 1, read and normalize. Parse both files. Restate each as a normalized list of transactions with consistent fields (trade date, settle date, instrument, identifier, quantity, gross amount, income type, withholding, account). Flag any field you had to infer. Do not compare yet.
>
> Pass 2, critique and surface breaks. Compare the two normalized lists. Produce a table of every discrepancy. For each, give: the field that differs, both values, and a first classification of the likely cause drawn only from the cause taxonomy I provide below. If the cause is unclear, mark it "unclassified" rather than guessing.
>
> Pass 3, propose and stage. For each break, propose a remediation path (UI, XML update, SQL query, or plugin) using the routing rules I provide below, with a one-line reason. Assign a confidence (high, medium, low). Add an empty "analyst sign-off" column. Do not assert that any break is resolved; every row is a proposal for human review.
>
> Output: the break table only, sorted by confidence descending, followed by a short note listing anything you could not classify and what you would need to classify it.
>
> [INSERT: cause taxonomy]
> [INSERT: remediation routing rules]
> [INSERT: income-type to tax-form mapping, e.g. 1099-DIV, 1042-S]

**domain_gap:**

> The three bracketed inserts are the asset. The source agent has none of them, and they are exactly what the analyst knows and the repo cannot. Supply: (1) the firm's break-cause taxonomy; (2) the rules that decide UI versus XML versus SQL versus plugin remediation; (3) the mapping from income type and account classification to the correct tax form and withholding treatment. Until these are filled, the skill is a competent generalist; once filled, it is role-specific and defensible.

Note for the evaluator: this exemplar passes all three tests visibly. It is understandable (a plain three-pass procedure), decomposed (the core function names no tool), and adaptable (the domain-gap note states precisely what the analyst pours in). An entry that cannot show all three is not ready.

The shipped entry, `content/entries/gl-reconciler-break-triage.yaml`, has since filled the cause-taxonomy insert with a fourteen-cause taxonomy built on the correction-loop pattern; the remediation-routing and tax-form-mapping inserts stay open as the terminal form. The three-insert version above remains the illustration of shape and depth for new entries.

---

## 9. Build pipeline

1. Write one YAML content file per entry in `content/entries/`, following the schema. One entry per asset.
2. Write the HTML template once: inlined CSS, the expandable-block component, the copy-button script, the filter and search controls.
3. Write the Python build script: read content, run the full validation in sections 4 and 5, loop over entries, inject into the template, run the offline check, emit one self-contained HTML file. A failed offline check aborts before any file is written.
4. Run, then verify against section 10. `python -m pytest` runs the contract tests behind each validation rule.
5. Iterate by editing content and re-running. The template and script change rarely.

---

## 10. Acceptance criteria

The evaluator should treat each as pass or fail. Reviewed 2026-08-04: all ten pass against the 23-entry build. Criteria 1 through 5 and 8 run as automated checks on every build, each backed by a contract test; 6, 7, 9, and 10 were verified by inspection of the template, the compiled page, and the shipped entries.

1. Every entry carries all required schema fields.
2. Every `core_function` is tool-agnostic.
3. Every finance asset has a substantive `domain_gap`. No entry implies out-of-the-box tax awareness.
4. Every workflow with a remediation step has an explicit human-sign-off gate.
5. The output file runs offline from `file://` with no external dependency.
6. Copy buttons yield clean plain text with no markup or smart-quote corruption.
7. Content and presentation are separable; entries are editable without touching the template.
8. Tier tags are present and are an integer 1 to 4. The tier reflects source credibility, with the rationale carried in each entry's `source` and `maturity` fields. The deep-research inventory that informed the first tiers is a research-phase artifact, not a build input, so no external file is required to verify this.
9. Primary navigation is by workflow stage; tier is a tag, not the axis.
10. At least one entry meets the depth of the section 8 exemplar, and the rest match its shape.

Bracketed `[INSERT: …]` placeholders in an `adapt` or `author-from-spec` entry are the intended terminal form, not an incomplete state. They mark the adaptation surface where firm-specific domain knowledge gets supplied at use time, drawn from `.claude/skills/tax-ops-domain.md`. An entry with open inserts passes criterion 1 and 10; the inserts are the asset, and the `domain_gap` note names what fills them.

---

## 11. Open questions, resolved

All four closed during the build. Recorded here so the recommendations and the decisions stay together.

1. Content format: YAML front-matter plus Markdown body, or a single JSON array. Recommendation: YAML plus Markdown, for readability during review and clean multi-line prompt bodies. Decided differently: one plain YAML file per entry in `content/entries/`, with block scalars carrying the multi-line bodies. Cleaner than front-matter for prompt-heavy entries, and one file per asset keeps diffs small.
2. v1 scope: author the full inventory now, or ship a focused first subset. Recommendation: a focused v1 covering the highest-fit assets across all four stages, chosen with the group, then expand. Breadth later, depth first. Decided as recommended: seven entries shipped 2026-06-03, widened to 23 by 2026-06-18.
3. Single output file versus a small set of linked files. Recommendation: single file, for the offline and portability promise. Decided as recommended: `dist/skills-library.html` is the whole artifact.
4. Whether to include a short "how to adapt an asset" preamble in the file that restates the three tests for any colleague who opens it cold. Recommendation: yes, one short panel at the top. Decided as recommended: shipped as a collapsible "How to adapt an asset" panel at the top of the page.

---

## 12. Versioning roadmap

- **v1:** Tool-agnostic content. Bodies run on whatever assistant the user has, including the current GS internal assistant and Copilot. Shipped 2026-06-03; 23 entries as of the 2026-08-04 review.
- **v2:** Add per-asset execution notes for specific tools as access is confirmed. In motion: `docs/retrieval-guidance.md` records verified M365 Copilot and SharePoint-agent grounding guidance.
- **v3:** When Claude or an internal Goldman tool lands, add execution notes for it and, where a real skill or agent file becomes runnable, link it alongside the prompt body. The content layer carries forward unchanged; only the execution notes grow. An early step exists: the `plugins/` tree packages the domain packs and the shared domain skill for Claude-native use, with the content layer untouched.

---

## 13. Review record, 2026-08-04

Evaluator pass, run against the as-built repo rather than the plan alone: the 23 entries under `content/entries/`, `build/build.py`, `build/template.html`, `tests/test_validate.py`, plus a fresh `--check` and pytest run. Both green: 23 entries validate, 23 contract tests pass.

Verdict: pass on all ten section 10 criteria. The plan held through the build. The separations it called for (content from presentation, decomposed core from domain gap, stage as the navigation axis) are visible in the shipped artifact.

Findings, all incorporated in place:

1. The content-format question was decided differently from the recommendation: plain YAML per entry, no front-matter, no JSON array. Sections 2, 9, and 11 now record the decision.
2. Validation grew past the spec's description. The two evaluator rules and the structural rules run as automated checks, each with a contract test. Sections 4, 5, and 7 now state what is enforced.
3. The shipped exemplar advanced past the section 8 version: the cause-taxonomy insert is filled; two inserts stay open as the terminal form. Section 8 notes the drift.
4. Navigation shipped with a Type filter row and prompt-text search beyond the section 6 plan. Section 6 now matches the page.
5. All four section 11 questions closed: three as recommended, the format question with a different answer found at build time.
6. Review feedback on this pass surfaced a validator gap behind the section 4 claim: the stage allowed-value check ran only for assets, so a workflow with an unknown stage validated and then dropped out of the rendered stage groups. The check now runs for every entry type, with new contract tests for the stage and adaptation enums.

Out of scope for this pass: the documentation drift between CLAUDE.md, the project dossier, and the plugin tree is tracked in TASKS.md and `docs/project-state.md` and stays with that task.

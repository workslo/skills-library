# content/harvest

Raw harvested source material. The build does not read this folder.

`build/build.py` compiles only `content/entries/`. Everything here is un-adapted source, treated as a specification per the three-test framework in `docs/north-star.md`: harvest the decomposition, drop what will not run on the tools at hand, and re-express the rest as an on-domain entry in `content/entries/`. The exclusion is intentional, not an oversight.

## writing-skills

Generic third-party writing skills in the folder-based `<name>/SKILL.md` format (`copywriting`, `content-strategy`, `deep-write`). As written they are off the cost-basis, 1099, and 1042-S domain. They have been decomposed and adapted into on-domain tax-ops entries:

- `copywriting` -> `content/entries/client-communication-drafter.yaml`
- `content-strategy` -> `content/entries/desk-kb-content-planner.yaml`
- `deep-write` -> `content/entries/iterative-tax-memo-writer.yaml`

The source files stay here as provenance. The adapted entries are what ships.

## bpa-generator

The reconstructed orchestration spec for the desk's Business Process Analysis
generator, the pipeline that produced the G&L Exceptions and Convey Report
Review analyses. The original runs as a staged graph (gate, extraction,
normalizer, nine parallel section writers, deterministic assembly) over a
typed shared state, with a runnable rebuild in the `agent-skills/` harvest
clone. None of that stack runs on a desk machine, so the harvest decomposes
it into prompt-only entries:

- ingestion stage (gate, extractors, normalizer) -> `content/entries/procedure-fact-normalizer.yaml`
- automation recommender + fit evaluator (W8, W9) -> `content/entries/process-improvement-fit-assessor.yaml`
- the full orchestration -> `content/entries/business-process-analysis-workflow.yaml`

`orchestration-spec.md` preserves the spec text (converted from the source
PDF; block order restored where text extraction interleaved). The seven
remaining writer prompts (W1 to W7) live there in full for a later widening
pass; today they ride as condensed inline prompts in the workflow entry.

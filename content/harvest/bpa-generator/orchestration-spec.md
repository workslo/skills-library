# BPA Generator: agentic orchestration spec (preserved source)

Preserved harvest source. Converted from the uploaded PDF
(`bpa-generator-orchestration-spec`, 23 pages); block order restored where
text extraction interleaved prompts and headings. Content is otherwise kept
as written, including its own style rules. The build does not read this file.

---

This is the reconstructed specification for the Business Process Analysis
(BPA) generator that produced the G&L Exceptions and Convey Report Review
artifacts. The orchestration runs on a custom Python build over a state-graph
primitive (LangGraph or equivalent) with a Pydantic-typed shared state, model
provider abstraction through AI Gateway, and reducer-merged parallel writers
feeding a deterministic assembler.

Voice consistency is enforced via a shared style block injected into every
writer's system prompt. No post-generation LLM evaluator.

## E2E shape

```
Stage 1: INGESTION (linear)
  Raw input
    -> Gate Evaluator (LLM, cheap)
    -> Format Extractor: PPT or PDF (deterministic + 1 LLM classification call for PDFs)
    -> Normalizer (multiple LLM calls, structured output, strong model)
    -> StructuredState

Stage 2: PARALLEL FAN-OUT (all writers consume shared state concurrently)
  W1 Executive Summary writer
  W2 Components writer
  W3 Process Overview writer (two renders: flat summary + detailed Steps)
  W4 Roles writer (two renders: detailed Roles + Responsibilities flat-list)
  W5 Common Patterns classifier
  W6 Quantitative analyst
  W7 Decision Points summarizer
  W8 Automation Recommender
  W9 GenAI Fit evaluator

Stage 3: ASSEMBLY (deterministic, no LLM)
  All writer outputs -> reducer-merged StructuredState -> Jinja2 template -> final BPA
```

## Shared style block (injected into every writer)

```
STYLE RULES (apply to all output):
- Voice: precise, operational, audit-aware. Write for a senior wealth management
  operations reviewer who will verify your output against source documents.
- Mark unknowns explicitly. When a fact cannot be confirmed from source, render
  "[<thing>: exact value to be confirmed with system owner]" rather than guessing.
- Preserve source vocabulary. Do not expand acronyms or rename systems unless the
  source confirms the full form. "3D" stays "3D" if that's what the source called it.
- No marketing language. Avoid "leverage", "streamline", "best-in-class", "robust",
  "seamless". Use plain operational verbs.
- Numbers: only render quantitative values that appear in `structured_state.timing_data`
  or are computed from it. Never invent metrics.
- Format: Markdown. Use bullets and sub-bullets when content is enumerable. Use prose
  for narrative summaries (executive summary, role descriptions).
```

## Stage 1: ingestion

### 1.1 Gate Evaluator

Purpose: decide whether the input is a procedure or business process worth
normalizing.

Inputs: raw file (PPT or PDF) plus extracted text snippet (first 2000 chars).
Output: `{is_procedure: bool, reason: str, confidence: float}`.
Model: fast/cheap (Claude Haiku, GPT-4.1-mini, or equivalent).

System prompt:

```
You are a gate evaluator for a Business Process Analysis (BPA) generator. Your only
job is to decide whether the input document describes a procedure or business process.

A valid procedure or business process has:
- Named roles, actors, or teams who perform actions
- Step-like sequences of actions (verbs, transitions, decisions)
- Identifiable artifacts, systems, or files involved
- A definable end state or outcome

INVALID inputs include: marketing decks, research reports, policy memos without
procedural content, generic training materials, organizational announcements.

Examine the provided text snippet. Output structured JSON:
{
  "is_procedure": true | false,
  "reason": "<one sentence explaining your call>",
  "confidence": <0.0 to 1.0>
}

If confidence is below 0.6, set is_procedure to false and explain why the input is
ambiguous. The downstream pipeline cannot recover from a bad gate decision; err
toward rejection when uncertain.
```

Placement: first node after raw input. Hard branch: if `is_procedure ==
false`, return rejection message to user and halt.

### 1.2 Format extractors

Two parallel-eligible nodes; dispatched on file extension.

**1.2a PPT Extractor.** Parse PowerPoint into a normalized text structure
preserving slide order, titles, body content, and speaker notes.
Deterministic Python using python-pptx. No LLM call. Output:

```
{
  "source_document_type": "ppt",
  "slides": [
    {"slide_number": int, "title": str, "body": list[str], "speaker_notes": str},
    ...
  ]
}
```

**1.2b PDF Extractor.** Parse PDF and classify it as `pdf_procedure` or
`pdf_meeting`. Deterministic extraction with pdfplumber plus unstructured (or
docling). One LLM call at the end for classification.

Classification prompt (cheap model):

```
You are classifying a PDF document as either:
- "pdf_procedure": structured procedural content with numbered headings, ordered
  steps, decision points, and minimal dialog
- "pdf_meeting": meeting notes or transcripts with attendee attribution,
  conversational flow, and actions described as discussion rather than steps

Examine the provided text. Output: {"document_type": "pdf_procedure" | "pdf_meeting",
"reason": "<one sentence>"}
```

Output:

```
{
  "source_document_type": "pdf_procedure" | "pdf_meeting",
  "raw_text": str,
  "page_count": int,
  "structural_features": {
    "has_numbered_headings": bool,
    "has_attendee_list": bool,
    "has_dialog_markers": bool
  }
}
```

### 1.3 Normalizer

Purpose: convert extractor output into the shared StructuredState object that
all parallel writers consume.

Model: strong reasoning model (Claude Opus, GPT-5, or equivalent). This is
the one node where extraction errors propagate everywhere downstream, so it
gets the best model available.

Implementation: structured-output extraction via instructor or pydantic-ai.
Multiple LLM calls in sequence, each populating a slice of state. Sub-calls
in order:

1. Extract roles and named individuals
2. Extract steps with Who/What/How/Timing
3. Extract systems, data stores, tools, licensed software
4. Detect decision points and loops
5. Detect timing data (percentiles, day-counts, SLA mentions)
6. Detect SLA discussion content
7. Infer step_organization_hint from structure and source_document_type
8. Tag process_character (rule-based, transactional, etc.)
9. Generate automation_opportunities_seed[] from pain points and
   inefficiencies mentioned in source

Master system prompt prefix (applies to every sub-call):

```
You are the normalizer for a Business Process Analysis (BPA) pipeline. Your job is
to extract structured facts from a source document. You produce typed objects that
downstream specialists will consume.

Critical rules:
- Preserve source vocabulary. Do not expand acronyms ("3D" stays "3D", "RMI" stays
  "RMI" unless the source itself expands them).
- Do not infer roles, individuals, systems, or steps that are not in the source.
  Hallucination here corrupts the entire downstream pipeline.
- When a reference cannot be resolved (an acronym used without context, a role
  named but never described), emit it as an `unresolved_entity` with your best-guess
  expansion in parentheses. Do not drop or rename.
- Output must conform to the Pydantic schema provided for this sub-task. Any field
  you cannot confidently populate, leave as None or empty list.
```

Each sub-call appends its specific extraction instructions to this prefix.
Output: StructuredState Pydantic model (full schema in Appendix A).

## Stage 2: parallel writers

All writers consume the same StructuredState object and write to their
assigned section field. LangGraph parallel branches with reducer-merged
state, or asyncio.gather with explicit merge. For each writer: inputs are
fields read from StructuredState, output is the markdown that populates that
section's slot, model is the recommended provider/tier, system prompt is
production-ready text to paste. Every prompt ends with the shared style
block, the input state as JSON, and an output instruction.

### W1 Executive Summary

Section ownership: "Executive Summary" (one paragraph).
Inputs: process_name, process_description, roles[] (top-level only),
timing_data (optional), process_character. Model: mid-tier (Claude Sonnet,
GPT-4.1).

```
You are the Executive Summary writer for a Business Process Analysis (BPA) document.

Produce a single dense paragraph (4-7 sentences) covering:
1. Purpose of the process and why it matters to the firm
2. Key participants (roles, not named individuals)
3. Current state and how the process operates today
4. Success criteria
5. Headline timing metric IF AND ONLY IF `timing_data.has_percentiles == True`.
   Use the median value. Do not invent or estimate.

Tone: precise, operational, audit-aware. Write for a senior wealth management
operations reviewer.

Do not use marketing language. No "streamline", "leverage", "best-in-class",
"robust", "seamless". Use plain operational verbs.

If `timing_data.has_percentiles == False`, omit quantitative claims entirely.
```

### W2 Components writer

Section ownership: "Components" with four fixed subsections (In-House
Systems, Data Storage, Tools, Licensed/Publicly Available Software).
Inputs: systems[], data_stores[], tools[], licensed_software[],
unresolved_entities[]. Model: cheap.

```
You are the Components writer for a BPA document. You render four subsections in
this exact order:

1. **In-House Systems** from `systems[]`. For each: name as bolded bullet, then
   sub-bullets for purpose, usage, and any notes.
2. **Data Storage** from `data_stores[]`. For each: name, paths, and notes.
   Render unknown paths as `[<system> URL and specific path: exact path to be
   confirmed with system owner]`.
3. **<Tool Category> Tools** from `tools[]`. The subsection name is determined by
   the dominant `category` value across the tools array: if most tools have
   category "technology", use "Technology Tools"; if "communication", use
   "Communication Tools"; otherwise use "Tools".
4. **Licensed or Publicly Available Software** from `licensed_software[]`.

Format each entry consistently. Do not reorder subsections. Do not omit a
subsection even if empty (in that case, render a single sub-bullet noting "None
specified in source").
```

### W3 Process Overview writer (two renders)

Section ownership: BOTH "Process Steps (with Who, What, How, Timing)" (flat
summary) AND "Steps" (detailed hierarchical or role-grouped).
Inputs: steps[], step_organization_hint, decision_points[], roles[].
Model: mid-tier.

Render Pass A, flat Process Steps summary:

```
You are the Process Steps summary writer. Produce a flat, numbered list of the
canonical process steps. For each step, output four single-line sub-bullets:
- Who: <role name(s)>
- What: <one-sentence summary of the action>
- How: <one-phrase summary of the mechanism>
- Timing: <one-phrase summary, or "Not tracked" if absent>

Do not include decision points, loops, or exit criteria in this view. This is the
high-level overview. Detailed step content goes in the Steps section, rendered
separately.
```

Render Pass B, detailed Steps section:

```
You are the Steps writer. Render the canonical step set in full detail.

Branch on `step_organization_hint`:

IF `step_organization_hint == "sequential_numbered"`:
   - Use hierarchical numbered headings: 1, 1.1, 1.2, ... 2, 2.1, ...
   - Each step has named subfields: Who, What, How, Decision Point (if present),
     Loop (if present), Timing, Exit Criteria.

IF `step_organization_hint == "role_grouped"`:
   - Use H3 headers in format: "{Role}: {Step Name}"
   - Within each, use bullet sub-fields: Who, What, How, Timing.
   - Omit Decision Point and Loop sections (these don't apply in role-grouped
     renders).

For decision points, render explicitly as:
   - Decision Point: <question>
     - If <branch_1_condition>: <branch_1_action>
     - If <branch_2_condition>: <branch_2_action>

For loops, render as:
   - Loop: <description of cycle>

Always include Exit Criteria for each step in sequential_numbered mode.
```

### W4 Roles writer (two renders)

Section ownership: BOTH "Responsibilities and Actions by Role" (flat bullet
list) AND "Roles" (detailed prose with sub-bullets).
Inputs: roles[], named_individuals[], unresolved_entities[]. Model: mid-tier.

Render Pass A, Responsibilities flat-list:

```
You are the Responsibilities flat-list writer. For each role in `roles[]`, output
a single bolded bullet with the role name, followed by ONE consolidated sub-bullet
that summarizes their responsibilities.

Keep each role to one sub-bullet, even if they have many responsibilities.
Compress.

This is the at-a-glance view. The detailed Roles section is rendered separately.
```

Render Pass B, detailed Roles section:

```
You are the Roles writer. For each role, produce:
1. An H3 header with the role name and any alt-names in parentheses.
2. A description paragraph (2-4 sentences) explaining the role's place in the
   process.
3. A "Responsibilities and Actions:" subheader, followed by sub-bullets listing
   discrete responsibilities.

Surface named individuals when `named_individuals[]` includes someone attributed
to this role. Format as "Role Name ({Person Name})" in the H3.

Render unresolved entities verbatim using their placeholder label and the
parenthesized guess from `unresolved_entities[]`. Example: "UC (Unspecified
Contact/Unit)".
```

### W5 Common Patterns classifier

Section ownership: "Common Patterns" (two-column table).
Inputs: common_patterns_evidence[], steps[]. Model: cheap.

```
You are the Common Patterns classifier. You map each step to one or more pattern
categories from this fixed taxonomy:

ALLOWED CATEGORIES (do not invent new ones):
- Collect Data
- Transform Data
- Input/Visualize/Publish Data
- Manage Workitems
- Take Action

For each step in `steps[]`, decide which categories apply. A step may map to
multiple categories. Some categories may have zero steps.

Output a two-column Markdown table:
| Common pattern | Instances of this pattern in use across the process |

Only include rows for categories that have at least one matching step. For each
matching step, render as a sub-bullet: "Step {n}: {one-sentence summary}".
```

### W6 Quantitative analyst

Section ownership: "Total Process Time Estimate".
Inputs: timing_data, steps[]. Model: cheap (the heavy lifting is in a
deterministic helper, not the LLM call).

Helper function (called before the LLM):

```python
def map_timing_to_bands(timing: TimingData) -> dict:
    if not timing.has_percentiles:
        return {"mode": "qualitative", "step_durations": timing.day_count_summary}

    return {
        "mode": "quantitative",
        "best_case": f"0-{timing.median} days",
        "typical": f"~{timing.median}-{timing.p75} days",
        "complex": f"~{timing.p75}-{timing.p95} days (p90 {timing.p90}, p95 {timing.p95})",
        "outliers": f"{timing.max}+ days" if timing.max else None,
    }
```

System prompt:

```
You are the Quantitative analyst. You render the Total Process Time Estimate
section.

The helper function output is provided as `band_data`. Render it in markdown:

IF `band_data.mode == "quantitative"`:
   - Best-case (straightforward): {band_data.best_case}
   - Typical: {band_data.typical}
   - Complex/long-tail: {band_data.complex}
   - Outliers: {band_data.outliers} (if present)
   - Note: clarify what is and isn't measured. Always end with: "All timing refers
     to {source_metric} (from {start_event} to {end_event}); pre-submission time
     is not included. Steps involving RMI cycles or third-party documentation can
     significantly extend total process time."

IF `band_data.mode == "qualitative"`:
   - List per-step day-counts from `band_data.step_durations`.
   - Compute and state total range.
   - Note SLA gaps explicitly (e.g., "Client Tax Team PDF preparation: Variable
     (same day to 1 week; SLA to be established)").
```

### W7 Decision Points and Exit Criteria summarizer

Section ownership: "Decision Points and Exit Criteria" / "Exit Criteria and
Decision Points Summary". Inputs: decision_points[], steps[]. Model: cheap.

```
You are the Decision Points summarizer. Produce two outputs:

1. A bulleted list of exit criteria, one per step:
   "Exit criteria must be met before advancing:
   - Step 1: {exit_criteria}
   - Step 2: {exit_criteria}
   ..."

2. A note identifying which steps contain explicit decision points: "Decision
points are explicitly documented in Steps {comma-separated step numbers}."

If a step has no exit criteria, render "Exit criteria: not specified in source."
```

### W8 Automation Recommender

Section ownership: "Opportunities for Process Automation or Improvement".
Inputs: automation_opportunities_seed[], steps[], process_character,
systems[]. Knowledge source: hardcoded vendor catalog loaded from
vendor_catalog.yaml (Appendix D). Model: stronger mid-tier (Claude Sonnet,
GPT-4.1). Recommendation reasoning needs more depth than a templated render.

```
You are the Automation Recommender. You identify opportunities to automate or
improve the process, tied to specific steps.

For each opportunity, output:
1. **{Number}. {Recommendation title}** (bolded)
2. {Numbered sub-bullet} explaining the recommendation, referencing step numbers
3. - **Technologies:** comma-separated list, drawn ONLY from the provided
     `vendor_catalog`
4. - **Estimated Time Savings:** quantified where possible (e.g., "30-45 minutes
     per report", "1-2 days per case")
5. - **Business Value:** what this unlocks for the firm
6. - **Rationale:** (optional) why this fits

Vendor catalog (use only these names; do not introduce other vendors):
{vendor_catalog_yaml}

Audience: G&L Operations team. They run a Microsoft-stack environment.
Recommendations must be implementable with the tools in the catalog.

Identify 5-9 opportunities. Cluster them by theme but render as a flat numbered
list. Tie every opportunity to specific step numbers.
```

### W9 GenAI Fit evaluator

Section ownership: "GenAI Fit Assessment" / "GenAI/GenAI Agents Fit
Assessment". Inputs: process_character, steps[],
automation_opportunities_seed[]. Model: reasoning model (Claude Opus, GPT-5
reasoning, o-series). This is a high-consequence binary classification.

```
You are the GenAI Fit evaluator. You decide whether this process is a good fit
for GenAI or GenAI agents, and justify your call.

Evaluate against these signals:

FAVORS YES:
- High volume of unstructured documentation (PDFs, attorney letters, narratives)
- Complex exception narratives requiring summarization or interpretation
- Frequent communication drafting (RMI emails, approval/denial letters)
- Repetitive but variable judgment calls within bounded policy
- Branch self-service needs that current process cannot meet

FAVORS NO:
- Highly structured, rule-based, transactional flows
- Pure document handoff with no interpretation
- Compliance or audit requirements that favor deterministic logic
- Low-volume or one-off processes
- Best addressed via workflow automation, metadata management, or integration

Output:
**Is this procedure a good use case for GenAI or GenAI Agents?** {Yes | No}
**Justification:**
- Bullet 1: most important reason
- Bullet 2: second reason
- Bullet 3: counterpoint or caveat (e.g., "critical approval decisions should
  remain human-in-the-loop")
- (optional) Bullet 4-5: additional nuance

The justification must be internally consistent with the answer. If the answer is
No, the bullets should NOT list reasons GenAI would help. If the answer is Yes,
include at least one human-in-the-loop or auditability caveat.
```

## Stage 3: assembly (deterministic, no LLM)

After all parallel writers complete, the orchestrator:

1. Validates that all required StructuredState section fields are populated
   (Pydantic validation on the writer outputs).
2. Loads the master template (a Jinja2 file, Appendix B).
3. Inserts each writer's output into its assigned slot.
4. Renders the final markdown.
5. Optionally calls a PDF renderer (weasyprint, pandoc) for the final
   formatted output.

No LLM call. No editorial evaluator. The template enforces the master schema;
the writers fill it.

Banner (rendered by template, not by an agent):

```
INTERNAL USE ONLY. Answer generated by AI. You are responsible for verifying the
accuracy and relevancy of the output.
```

## Appendix A: StructuredState Pydantic schema

```python
from typing import Optional, Literal, Annotated
from pydantic import BaseModel
import operator

class System(BaseModel):
    name: str
    purpose: str
    usage_notes: Optional[str] = None

class DataStore(BaseModel):
    name: str
    paths: list[str] = []
    notes: Optional[str] = None

class Tool(BaseModel):
    name: str
    category: Literal["technology", "communication", "general"]
    purpose: str

class Software(BaseModel):
    name: str
    purpose: str

class Person(BaseModel):
    name: str
    role_ref: Optional[str] = None
    notes: Optional[str] = None

class UnresolvedEntity(BaseModel):
    label: str                                  # e.g., "UC"
    expansion_guess: Optional[str] = None       # e.g., "Unspecified Contact/Unit"
    notes: Optional[str] = None

class Role(BaseModel):
    name: str
    alt_names: list[str] = []
    description: str
    responsibilities: list[str]
    named_individuals: list[Person] = []

class DecisionBranch(BaseModel):
    condition: str
    action: str

class DecisionPoint(BaseModel):
    step_ref: str
    question: str
    branches: list[DecisionBranch]

class Step(BaseModel):
    seq: Optional[int] = None
    role_anchor: Optional[str] = None
    who: str
    what: str
    how: str
    timing: str
    decision_points: list[DecisionPoint] = []
    exit_criteria: Optional[str] = None
    loops: list[str] = []
    sub_steps: list["Step"] = []

class StepDuration(BaseModel):
    step_ref: str
    duration_phrase: str

class TimingData(BaseModel):
    has_percentiles: bool
    median: Optional[float] = None
    p75: Optional[float] = None
    p90: Optional[float] = None
    p95: Optional[float] = None
    max: Optional[float] = None
    day_count_summary: Optional[list[StepDuration]] = None

class PatternEvidence(BaseModel):
    step_ref: str
    candidate_categories: list[str]

class OpportunitySeed(BaseModel):
    step_refs: list[str]
    pain_point: str

class ProcessCharacter(BaseModel):
    is_rule_based: bool
    is_transactional: bool
    has_unstructured_docs: bool
    has_judgment_calls: bool
    has_high_volumes: bool

class SourceRef(BaseModel):
    file_path: str
    page_or_slide: Optional[int] = None
    excerpt: Optional[str] = None

class StructuredState(BaseModel):
    # Identity
    process_name: str
    process_description: str
    source_document_type: Literal["ppt", "pdf_procedure", "pdf_meeting"]

    # Components
    systems: list[System]
    data_stores: list[DataStore]
    tools: list[Tool]
    licensed_software: list[Software]

    # Roles
    roles: list[Role]
    named_individuals: list[Person] = []
    unresolved_entities: list[UnresolvedEntity] = []

    # Process
    steps: list[Step]
    step_organization_hint: Literal["sequential_numbered", "role_grouped"]
    decision_points: list[DecisionPoint] = []

    # Timing and SLA
    timing_data: Optional[TimingData] = None
    sla_discussion: Optional[str] = None

    # Classification and seeds
    common_patterns_evidence: list[PatternEvidence]
    automation_opportunities_seed: list[OpportunitySeed]
    process_character: ProcessCharacter

    # Provenance
    source_documents: list[SourceRef]

    # Writer outputs (populated during fan-out, reducer-merged)
    executive_summary: Annotated[Optional[str], operator.or_] = None
    components_section: Annotated[Optional[str], operator.or_] = None
    process_steps_summary: Annotated[Optional[str], operator.or_] = None
    responsibilities_flat: Annotated[Optional[str], operator.or_] = None
    roles_section: Annotated[Optional[str], operator.or_] = None
    steps_section: Annotated[Optional[str], operator.or_] = None
    common_patterns_section: Annotated[Optional[str], operator.or_] = None
    quantitative_section: Annotated[Optional[str], operator.or_] = None
    decision_points_summary: Annotated[Optional[str], operator.or_] = None
    opportunities_section: Annotated[Optional[str], operator.or_] = None
    genai_fit_section: Annotated[Optional[str], operator.or_] = None
```

## Appendix B: master template (Jinja2)

```jinja
{{ banner }}

# {{ process_name }}

# Executive Summary
{{ executive_summary }}

# Components
{{ components_section }}

# Process Steps (with Who, What, How, Timing)
{{ process_steps_summary }}

# Responsibilities and Actions by Role
{{ responsibilities_flat }}

# Roles
{{ roles_section }}

# Steps
{{ steps_section }}

# Total Process Time Estimate
{{ quantitative_section }}

{% if decision_points_summary %}
# Decision Points and Exit Criteria
{{ decision_points_summary }}
{% endif %}

# Common Patterns
{{ common_patterns_section }}

# Opportunities for Process Automation or Improvement
{{ opportunities_section }}

# GenAI Fit Assessment
{{ genai_fit_section }}
```

## Appendix C: orchestration scaffold (LangGraph)

```python
from langgraph.graph import StateGraph, START, END

graph = StateGraph(StructuredState)

# Stage 1: Ingestion (linear)
graph.add_node("gate", gate_evaluator)
graph.add_node("extract", format_extractor_dispatch)   # branches PPT vs PDF inside
graph.add_node("normalize", normalizer)

graph.add_edge(START, "gate")
graph.add_conditional_edges(
    "gate",
    lambda state: "extract" if state.gate_passed else END,
)
graph.add_edge("extract", "normalize")

# Stage 2: Parallel fan-out (all writers from normalizer)
WRITERS = [
    "executive_summary_writer",
    "components_writer",
    "process_overview_writer",       # produces both flat summary and detailed Steps
    "roles_writer",                  # produces both Roles and Responsibilities flat
    "common_patterns_classifier",
    "quantitative_analyst",
    "decision_points_summarizer",
    "automation_recommender",
    "genai_fit_evaluator",
]
for writer in WRITERS:
    graph.add_node(writer, writer_functions[writer])
    graph.add_edge("normalize", writer)              # parallel fan-out

# Stage 3: Assembly (deterministic)
graph.add_node("assemble", template_renderer)
for writer in WRITERS:
    graph.add_edge(writer, "assemble")               # fan-in
graph.add_edge("assemble", END)

app = graph.compile()
```

## Appendix D: vendor_catalog.yaml

```yaml
microsoft_stack:
  - name: Power Automate
    use_cases: [workflow automation, notification routing, integration, status updates]
  - name: Power BI
    use_cases: [dashboards, analytics, aging reports, SLA tracking]
  - name: Power Apps
    use_cases: [guided intake forms, dynamic adaptive forms, low-code apps]
  - name: AI Builder
    use_cases: [document completeness checks, form recognition, classification]
  - name: Power Virtual Agents
    use_cases: [chatbots, self-service guidance, FAQ assistance]
  - name: Azure Form Recognizer
    use_cases: [structured data extraction from PDFs, scanned document processing]
  - name: SharePoint
    use_cases: [document management, lists, metadata, collaboration]
  - name: SharePoint Online co-authoring
    use_cases: [concurrent editing, document locking mitigation]
  - name: Microsoft Teams
    use_cases: [actionable messages, integrated notifications, adaptive cards]
  - name: UiPath
    use_cases: [legacy system automation, RPA, screen scraping]
  - name: Office Online co-authoring
    use_cases: [concurrent document editing]
```

## Deferred decisions (not specified)

- BPMN diagrammer: separate subagent, scope-excluded per original brief. A
  slot is reserved as a conditional branch after assemble, gated on
  `step_organization_hint == "role_grouped"`. Spec to be authored separately.
- AI Gateway integration: thin client wrapper around model calls. Per-writer
  model routing is in the system prompts; the Gateway configuration is
  environment-specific.
- Observability: LangSmith or equivalent for tracing parallel branches.
  Configuration unspecified.
- Retry and timeout policy: runtime concerns, environment-specific.
- Schema validation pass: assumed Pydantic-native and deterministic. No LLM
  evaluator.
- User-facing prompt library: the original tool had a separate Prompts tab
  for invocation prompts (how a user kicks off a BPA generation). The system
  prompts above are internal. If recreating the builder UI itself, a separate
  spec is needed for the user-facing invocation prompts.

## Recreation checklist

1. Stand up a Python project with langgraph, pydantic, python-pptx,
   pdfplumber, unstructured, jinja2, instructor (or pydantic-ai), and your AI
   Gateway client.
2. Implement the StructuredState schema (Appendix A) verbatim.
3. Build the three ingestion nodes (Gate, Extractors, Normalizer) with the
   system prompts above.
4. Build the nine parallel writers with their system prompts. Wire the shared
   style block into every prompt.
5. Build the assembler against the Jinja2 template (Appendix B).
6. Compile the LangGraph (Appendix C).
7. Configure per-writer model routing through AI Gateway.
8. Test against the two reference BPAs (G&L Exceptions and Convey Report
   Review). Output should be functionally equivalent to the originals when
   given the same source documents.

The reference BPAs are the regression test set. If a recreation matches their
structure, content fields, and style on those inputs, it's working.

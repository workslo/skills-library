#!/usr/bin/env python3
# Build the Skills Library into one self-contained, offline HTML file.
#
# Install dependencies once:
#   pip install pyyaml markdown
#
# Usage:
#   python build/build.py           validate, then build dist/skills-library.html
#   python build/build.py --check   validate only, no build
#
# Exit code is 0 on success and non-zero on any validation or offline-check
# failure, with the failing file, field, and rule named.

import argparse
import html
import re
import sys
from pathlib import Path

import yaml
import markdown

# Paths are resolved from the repo root, the parent of this file's directory.
ROOT = Path(__file__).resolve().parent.parent
# The build reads only content/entries. memory/ is operator context, never compiled.
CONTENT_DIR = ROOT / "content" / "entries"
TEMPLATE = ROOT / "build" / "template.html"
OUTPUT = ROOT / "dist" / "skills-library.html"

# The four workflow stages. Primary navigation axis.
STAGES = ["intake-classify", "research", "remediate", "communicate"]
TIERS = [1, 2, 3, 4]
ASSET_TYPES = ["prompt", "skill", "agent", "workflow"]
ADAPTATIONS = ["use-as-is", "adapt", "author-from-spec"]

# Required fields by entry type. See SKILLS_LIBRARY_SPEC.md sections 4 and 5.
COMMON_REQUIRED = ["id", "name", "type", "stage", "tier", "source", "domain_fit", "maturity"]
ASSET_REQUIRED = COMMON_REQUIRED + ["core_function", "adaptation", "body", "domain_gap"]
WORKFLOW_REQUIRED = COMMON_REQUIRED + ["trigger", "steps", "gates", "output"]

# A core_function naming any of these has not been decomposed to a tool-agnostic
# core. Matched on word boundaries against the lowercased text.
TOOL_TOKENS = [
    "sql", "xml", "plugin", "database", "connector", "runtime",
    "sdk", "mcp", "api", "rest", "graphql", "endpoint", "cron",
]

# A domain_gap shorter than this many characters is treated as non-substantive.
DOMAIN_GAP_MIN_CHARS = 60

# Words that signal a remediation step inside a workflow. A workflow with a
# remediation step and no sign-off gate is a defect.
REMEDIATION_WORDS = [
    "remediate", "remediation", "correct", "update", "fix",
    "post", "submit", "write", "book", "adjust", "amend",
]

MD = markdown.Markdown(extensions=["extra", "sane_lists"])


def render_md(text):
    # Render a Markdown string to HTML. Reset keeps state clean between calls.
    MD.reset()
    return MD.convert(str(text).strip())


def load_entry(path):
    # Load one entry. Pure YAML files carry every field as a key. Markdown files
    # carry YAML front-matter between the first two --- fences and the body after.
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        data = yaml.safe_load(raw) or {}
    else:
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.DOTALL)
        if not m:
            raise ValueError("Markdown entry is missing --- front-matter fences.")
        data = yaml.safe_load(m.group(1)) or {}
        data["body"] = m.group(2).strip()
    if not isinstance(data, dict):
        raise ValueError("Entry did not parse to a mapping.")
    data["_file"] = str(path.relative_to(ROOT))
    return data


def load_entries():
    if not CONTENT_DIR.exists():
        return []
    files = sorted(
        p for p in CONTENT_DIR.iterdir()
        if p.suffix.lower() in (".yaml", ".yml", ".md")
    )
    entries = []
    for p in files:
        try:
            entries.append(load_entry(p))
        except Exception as exc:  # noqa: BLE001
            entries.append({"_file": str(p.relative_to(ROOT)), "_parse_error": str(exc)})
    return entries


def validate_entries(entries):
    # Return a list of (file, field, message). Empty list means every entry passed.
    errors = []
    seen_ids = {}

    for e in entries:
        f = e.get("_file", "<unknown>")

        if "_parse_error" in e:
            errors.append((f, "-", "parse failed: " + e["_parse_error"]))
            continue

        etype = e.get("type")
        required = WORKFLOW_REQUIRED if etype == "workflow" else ASSET_REQUIRED

        for field in required:
            val = e.get(field)
            if val is None or (isinstance(val, str) and not val.strip()):
                errors.append((f, field, "required field is missing or empty"))

        if etype not in ASSET_TYPES:
            errors.append((f, "type", "must be one of " + ", ".join(ASSET_TYPES)))

        # Stable, unique id that matches the filename stem.
        eid = e.get("id")
        if eid:
            stem = Path(f).stem
            if eid != stem:
                errors.append((f, "id", "id '%s' does not match filename stem '%s'" % (eid, stem)))
            if eid in seen_ids:
                errors.append((f, "id", "duplicate id, also used by " + seen_ids[eid]))
            seen_ids[eid] = f

        # Accept an int or a string that names an int, matching the renderer,
        # which coerces with int(). A quoted tier in YAML must not be a hard fail.
        try:
            tier_ok = int(e.get("tier")) in TIERS
        except (TypeError, ValueError):
            tier_ok = False
        if not tier_ok:
            errors.append((f, "tier", "must be an integer 1 to 4"))

        # Asset-specific rules.
        if etype != "workflow":
            stage = e.get("stage")
            if stage and stage not in STAGES:
                errors.append((f, "stage", "must be one of " + ", ".join(STAGES)))

            adaptation = e.get("adaptation")
            if adaptation and adaptation not in ADAPTATIONS:
                errors.append((f, "adaptation", "must be one of " + ", ".join(ADAPTATIONS)))

            cf = str(e.get("core_function", "")).lower()
            for tok in TOOL_TOKENS:
                # Trailing s? catches plurals so "calls external APIs" still trips.
                if re.search(r"\b" + re.escape(tok) + r"s?\b", cf):
                    errors.append((f, "core_function", "names a tool ('%s'); not decomposed" % tok))

            gap = str(e.get("domain_gap", "")).strip()
            if gap and len(gap) < DOMAIN_GAP_MIN_CHARS:
                errors.append((f, "domain_gap", "too thin to be substantive; finance assets need a real gap note"))

        # Workflow-specific rules.
        else:
            steps = e.get("steps") or []
            gates = e.get("gates") or []
            if not isinstance(steps, list) or not steps:
                errors.append((f, "steps", "workflow needs an ordered list of steps"))
            has_remediation = False
            for s in steps if isinstance(steps, list) else []:
                # Scan title, prompt, and output. Remediation described only in a
                # step's output must still demand a gate.
                blob = " ".join(
                    str(s.get(k, "")) for k in ("title", "prompt", "output")
                ).lower()
                if any(re.search(r"\b" + re.escape(w) + r"\b", blob) for w in REMEDIATION_WORDS):
                    has_remediation = True
            if has_remediation and not gates:
                errors.append((f, "gates", "workflow has a remediation step but no human-sign-off gate"))
            elif not gates:
                errors.append((f, "gates", "workflow needs at least one explicit sign-off gate"))

    return errors


def tag(label, cls):
    return '<span class="tag %s">%s</span>' % (cls, html.escape(label))


def search_text(*items):
    chunks = []
    for item in items:
        if item is None:
            continue
        if isinstance(item, list):
            for value in item:
                if isinstance(value, dict):
                    chunks.extend(str(v) for v in value.values())
                else:
                    chunks.append(str(value))
        elif isinstance(item, dict):
            chunks.extend(str(v) for v in item.values())
        else:
            chunks.append(str(item))
    return html.escape(" ".join(chunks).lower(), quote=True)


def safe_id(value):
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", str(value)).strip("-")


def render_asset(e):
    eid = safe_id(e.get("id", "asset"))
    name = html.escape(str(e.get("name", "")))
    etype = html.escape(str(e.get("type", "")))
    stage = str(e.get("stage", ""))
    tier = int(e.get("tier", 0))
    adaptation = html.escape(str(e.get("adaptation", "")))
    core = html.escape(str(e.get("core_function", "")).strip())
    search = search_text(
        e.get("name", ""), e.get("core_function", ""), e.get("body", ""),
        e.get("domain_gap", ""), e.get("domain_fit", ""), e.get("notes", "")
    )

    body_raw = html.escape(str(e.get("body", "")).rstrip("\n"))
    gap = render_md(e.get("domain_gap", ""))
    fit = render_md(e.get("domain_fit", ""))
    maturity = render_md(e.get("maturity", ""))
    source = html.escape(str(e.get("source", "")))
    notes = e.get("notes")
    notes_html = render_md(notes) if notes else ""

    parts = []
    parts.append('<article class="card" data-stage="%s" data-tier="%d" data-type="%s" data-search="%s">'
                 % (html.escape(stage, quote=True), tier, html.escape(etype, quote=True), search))
    parts.append('<button class="card-open" type="button" data-dialog="%s-dialog">' % eid)
    parts.append('<span class="summary-head">')
    parts.append('<span class="name">%s</span>' % name)
    parts.append('<span class="tags">%s%s%s</span>'
                 % (tag(etype, "t-type"), tag(stage, "t-stage"), tag("tier " + str(tier), "t-tier tier-%d" % tier)))
    parts.append('</span>')
    parts.append('<span class="core">%s</span>' % core)
    parts.append('<span class="adapt">%s</span>' % adaptation)
    parts.append('</button>')

    parts.append('<dialog class="detail" id="%s-dialog">' % eid)
    parts.append('<div class="dialog-head">')
    parts.append('<div>')
    parts.append('<h3>%s</h3>' % name)
    parts.append('<div class="dialog-tags">%s%s%s</div>'
                 % (tag(etype, "t-type"), tag(stage, "t-stage"), tag("tier " + str(tier), "t-tier tier-%d" % tier)))
    parts.append('</div>')
    parts.append('<button class="close" type="button" aria-label="Close">Close</button>')
    parts.append('</div>')

    parts.append('<div class="body-area">')
    parts.append('<div class="field"><h4>Core function</h4><p>%s</p></div>' % core)
    parts.append('<div class="copywrap">')
    parts.append('<button class="copy" type="button" data-copy="prompt" aria-live="polite">Copy prompt</button>')
    parts.append('<pre class="body">%s</pre>' % body_raw)
    parts.append('</div>')

    if fit:
        parts.append('<div class="field"><h4>Domain fit</h4>%s</div>' % fit)
    if gap:
        parts.append('<div class="field gap"><h4>Domain gap, what the analyst supplies</h4>%s</div>' % gap)
    parts.append('<div class="meta">')
    parts.append('<div class="field"><h4>Source</h4><p>%s</p></div>' % source)
    if maturity:
        parts.append('<div class="field"><h4>Maturity</h4>%s</div>' % maturity)
    if notes_html:
        parts.append('<div class="field"><h4>Notes</h4>%s</div>' % notes_html)
    parts.append('</div>')
    parts.append('</div>')
    parts.append('</dialog>')
    parts.append('</article>')
    return "\n".join(parts)


def render_workflow(e):
    eid = safe_id(e.get("id", "workflow"))
    name = html.escape(str(e.get("name", "")))
    tier = int(e.get("tier", 0))
    stage = str(e.get("stage", ""))
    trigger = render_md(e.get("trigger", ""))
    fit = render_md(e.get("domain_fit", ""))
    maturity = render_md(e.get("maturity", ""))
    source = html.escape(str(e.get("source", "")))
    output = render_md(e.get("output", ""))
    gates = e.get("gates") or []
    steps = e.get("steps") or []
    search = search_text(
        e.get("name", ""), e.get("trigger", ""), steps, gates, e.get("output", ""),
        e.get("domain_fit", ""), e.get("notes", "")
    )

    parts = []
    parts.append('<article class="card workflow" data-stage="%s" data-tier="%d" data-type="workflow" data-search="%s">'
                 % (html.escape(stage, quote=True), tier, search))
    parts.append('<button class="card-open" type="button" data-dialog="%s-dialog">' % eid)
    parts.append('<span class="summary-head">')
    parts.append('<span class="name">%s</span>' % name)
    parts.append('<span class="tags">%s%s%s</span>'
                 % (tag("workflow", "t-type"), tag(stage, "t-stage"), tag("tier " + str(tier), "t-tier tier-%d" % tier)))
    parts.append('</span>')
    parts.append('<span class="core">Trigger: %s</span>' % html.escape(str(e.get("trigger", "")).strip()))
    parts.append('</button>')

    parts.append('<dialog class="detail" id="%s-dialog">' % eid)
    parts.append('<div class="dialog-head">')
    parts.append('<div>')
    parts.append('<h3>%s</h3>' % name)
    parts.append('<div class="dialog-tags">%s%s%s</div>'
                 % (tag("workflow", "t-type"), tag(stage, "t-stage"), tag("tier " + str(tier), "t-tier tier-%d" % tier)))
    parts.append('</div>')
    parts.append('<button class="close" type="button" aria-label="Close">Close</button>')
    parts.append('</div>')

    parts.append('<div class="body-area">')
    parts.append('<button class="copy copy-all" type="button" data-copy="workflow" aria-live="polite">Copy whole workflow</button>')

    if trigger:
        parts.append('<div class="field"><h4>Trigger</h4>%s</div>' % trigger)

    parts.append('<ol class="steps">')
    for i, s in enumerate(steps, start=1):
        title = html.escape(str(s.get("title", "Step %d" % i)))
        ref = s.get("asset")
        ref_html = ' <span class="ref">uses %s</span>' % html.escape(str(ref)) if ref else ""
        prompt_raw = html.escape(str(s.get("prompt", "")).rstrip("\n"))
        out = html.escape(str(s.get("output", "")).strip())
        parts.append('<li class="step">')
        parts.append('<div class="step-head"><span class="step-n">%d</span><span class="step-title">%s%s</span></div>' % (i, title, ref_html))
        parts.append('<div class="copywrap">')
        parts.append('<button class="copy" type="button" data-copy="prompt" aria-live="polite">Copy step</button>')
        parts.append('<pre class="body">%s</pre>' % prompt_raw)
        parts.append('</div>')
        if out:
            parts.append('<div class="step-out">Output: %s</div>' % out)
        parts.append('</li>')
    parts.append('</ol>')

    if gates:
        parts.append('<div class="field gates"><h4>Human sign-off gates</h4><ul>')
        for g in gates:
            parts.append('<li>%s</li>' % html.escape(str(g)))
        parts.append('</ul></div>')

    if output:
        parts.append('<div class="field"><h4>Output</h4>%s</div>' % output)
    parts.append('<div class="meta">')
    parts.append('<div class="field"><h4>Source</h4><p>%s</p></div>' % source)
    if fit:
        parts.append('<div class="field"><h4>Domain fit</h4>%s</div>' % fit)
    if maturity:
        parts.append('<div class="field"><h4>Maturity</h4>%s</div>' % maturity)
    parts.append('</div>')
    parts.append('</div>')
    parts.append('</dialog>')
    parts.append('</article>')
    return "\n".join(parts)


def render_entries(entries):
    # Group by starting stage for the primary navigation axis. Type filtering
    # isolates workflows; they do not move to a synthetic workflow bucket.
    by_stage = {s: [] for s in STAGES}
    for e in entries:
        if e.get("stage") in STAGES:
            by_stage[e.get("stage")].append(e)

    blocks = []
    for s in STAGES:
        group = by_stage[s]
        if not group:
            continue
        blocks.append('<section class="stage-group" data-group="%s">' % html.escape(s, quote=True))
        blocks.append('<h2 class="stage-title">%s</h2>' % html.escape(s))
        blocks.append('<div class="card-grid">')
        for e in group:
            blocks.append(render_workflow(e) if e.get("type") == "workflow" else render_asset(e))
        blocks.append('</div>')
        blocks.append('</section>')
    return "\n".join(blocks)


# The (?:https?:)?// prefix catches both absolute (https://cdn) and
# protocol-relative (//cdn) external references.
OFFLINE_PATTERNS = [
    (r'src\s*=\s*["\']?\s*(?:https?:)?//', "external src attribute"),
    (r'href\s*=\s*["\']?\s*(?:https?:)?//', "external href attribute"),
    (r'<link\b', "link element"),
    (r'<script\b[^>]*\bsrc\s*=', "external script element"),
    (r'@import\b', "css @import"),
    (r'url\(\s*["\']?\s*(?:https?:)?//', "css url() to a remote resource"),
]

STORAGE_PATTERNS = [
    (r'\blocalStorage\b', "localStorage reference"),
    (r'\bsessionStorage\b', "sessionStorage reference"),
    (r'\bindexedDB\b', "indexedDB reference"),
    (r'\bdocument\.cookie\b', "document.cookie reference"),
]


def chrome_only(html_text):
    # Entry prose can legitimately mention URLs, CSS tokens, or storage APIs.
    # The offline contract applies to executable chrome: template, CSS, JS, and
    # renderer-owned attributes around the content block.
    return re.sub(
        r'(<main\b[^>]*id=["\']library["\'][^>]*>).*?(</main>)',
        r'\1<!-- entries omitted for offline scan -->\2',
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )


def check_offline(html_text):
    # Return a list of human-readable offline violations. Empty means clean.
    found = []
    scan_text = chrome_only(html_text)
    for pat, label in OFFLINE_PATTERNS + STORAGE_PATTERNS:
        for m in re.finditer(pat, scan_text, re.IGNORECASE):
            start = max(0, m.start() - 30)
            snippet = scan_text[start:m.start() + 40].replace("\n", " ")
            found.append("%s near: ...%s..." % (label, snippet.strip()))
    return found


def stage_count(entries):
    # Distinct workflow stages actually represented in the library, in STAGES order.
    present = {e.get("stage") for e in entries}
    return sum(1 for s in STAGES if s in present)


def build(entries):
    template = TEMPLATE.read_text(encoding="utf-8")
    cards = render_entries(entries)
    out = template.replace("<!--ENTRIES-->", cards)
    out = out.replace("<!--COUNT-->", str(len(entries)))
    out = out.replace("<!--STAGES-->", ",".join(STAGES))
    out = out.replace("<!--STAGE_COUNT-->", str(stage_count(entries)))
    return out


def print_report(errors, entries):
    if not errors:
        print("PASS. %d entries, every required field present, every rule clear." % len(entries))
        return True
    print("FAIL. %d issue(s) across %d entries. Build is blocked until they clear.\n"
          % (len(errors), len(entries)))
    for f, field, msg in errors:
        print("  %s  [%s]  %s" % (f, field, msg))
    print("")
    return False


def main():
    ap = argparse.ArgumentParser(description="Build the offline Skills Library HTML.")
    ap.add_argument("--check", action="store_true", help="validate only, do not build")
    args = ap.parse_args()

    entries = load_entries()
    if not entries:
        print("No entries found in %s. Add at least one before building."
              % CONTENT_DIR.relative_to(ROOT))
        sys.exit(1)

    errors = validate_entries(entries)
    ok = print_report(errors, entries)
    if not ok:
        sys.exit(1)

    if args.check:
        return

    if not TEMPLATE.exists():
        print("Template missing at %s." % TEMPLATE.relative_to(ROOT))
        sys.exit(1)

    out_html = build(entries)
    violations = check_offline(out_html)
    if violations:
        print("FAIL. Offline check found %d external reference(s). Build aborted.\n"
              % len(violations))
        for v in violations:
            print("  " + v)
        sys.exit(1)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(out_html, encoding="utf-8")
    print("Built %s" % OUTPUT.resolve())
    print("Entries: %d. Offline check: clean. Open it from file:// with no network."
          % len(entries))


if __name__ == "__main__":
    main()

"""Contract tests for validate_entries, the function the whole quality bar rests on.

Run from the repo root:
    pip install pyyaml markdown pytest
    python -m pytest

Each test crafts entry dicts and asserts which (file, field, message) tuples come
back. The fields named in the assertions are the rule under test.
"""

import sys
from pathlib import Path

# build.py lives in build/; add it to the path so we can import the validator.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "build"))

from build import build, check_offline, render_asset, render_entries, render_workflow, stage_count, validate_entries  # noqa: E402


def asset(**over):
    # A minimal asset entry that passes every rule. Override one field per test.
    e = {
        "_file": "demo-entry.yaml",
        "id": "demo-entry",
        "name": "Demo entry",
        "type": "prompt",
        "tier": 2,
        "source": "example/repo",
        "domain_fit": "Reconciliation, directly.",
        "maturity": "vendor-backed, active",
        "stage": "research",
        "core_function": "Compare two records and surface the differences.",
        "adaptation": "adapt",
        "body": "Do the thing.",
        "domain_gap": "Insert the break taxonomy, the routing rules, and the form mappings the analyst supplies.",
    }
    e.update(over)
    return e


def workflow(**over):
    e = {
        "_file": "demo-flow.yaml",
        "id": "demo-flow",
        "name": "Demo flow",
        "type": "workflow",
        "stage": "research",
        "tier": 1,
        "source": "example/repo",
        "domain_fit": "Reconciliation, directly.",
        "maturity": "vendor-backed, active",
        "trigger": "An inbound break lands in the queue.",
        "steps": [{"title": "Read the log", "prompt": "Read it."}],
        "gates": ["Analyst confirms the classification."],
        "output": "A classified break.",
    }
    e.update(over)
    return e


def fields(errors):
    return {field for _f, field, _m in errors}


def test_valid_asset_passes():
    assert validate_entries([asset()]) == []


def test_valid_workflow_passes():
    assert validate_entries([workflow()]) == []


def test_workflow_stage_is_required():
    e = workflow()
    del e["stage"]
    assert "stage" in fields(validate_entries([e]))


def test_missing_required_field_is_flagged():
    e = asset()
    del e["domain_fit"]
    assert "domain_fit" in fields(validate_entries([e]))


def test_unknown_type_is_flagged():
    assert "type" in fields(validate_entries([asset(type="macro")]))


def test_id_must_match_filename_stem():
    assert "id" in fields(validate_entries([asset(id="something-else")]))


def test_duplicate_id_is_flagged():
    errors = validate_entries([asset(), asset()])
    assert any("duplicate id" in m for _f, field, m in errors if field == "id")


def test_tier_out_of_range_is_flagged():
    assert "tier" in fields(validate_entries([asset(tier=9)]))


def test_quoted_tier_string_is_accepted():
    # Regression: a YAML-quoted tier ("2") must pass, matching the renderer's int().
    assert "tier" not in fields(validate_entries([asset(tier="2")]))


def test_tool_token_in_core_function_is_flagged():
    assert "core_function" in fields(
        validate_entries([asset(core_function="Query the SQL database for breaks.")])
    )


def test_plural_tool_token_is_flagged():
    # Regression: "APIs" must trip the scan, not just "API".
    assert "core_function" in fields(
        validate_entries([asset(core_function="Calls external APIs to fetch data.")])
    )


def test_thin_domain_gap_is_flagged():
    assert "domain_gap" in fields(validate_entries([asset(domain_gap="ask someone")]))


def test_remediation_without_gate_is_flagged():
    e = workflow(
        steps=[{"title": "Correct the cost basis", "prompt": "Apply the fix."}],
        gates=[],
    )
    assert "gates" in fields(validate_entries([e]))


def test_remediation_described_only_in_output_still_needs_a_gate():
    # Regression: remediation in the step output, not the title/prompt, must still
    # require a sign-off gate.
    e = workflow(
        steps=[{"title": "Step one", "prompt": "Look at it.",
                "output": "The corrected cost-basis record is posted."}],
        gates=[],
    )
    assert "gates" in fields(validate_entries([e]))


def test_render_asset_has_type_dialog_and_search_corpus():
    html = render_asset(asset(body="Research localStorage prose and withholding variance."))
    assert '<article class="card"' in html
    assert 'data-type="prompt"' in html
    assert '<dialog class="detail" id="demo-entry-dialog">' in html
    assert 'withholding variance' in html
    assert 'localstorage prose' in html


def test_render_workflow_keeps_starting_stage_and_type():
    html = render_workflow(workflow())
    assert 'class="card workflow"' in html
    assert 'data-stage="research"' in html
    assert 'data-type="workflow"' in html
    assert '<dialog class="detail" id="demo-flow-dialog">' in html


def test_render_entries_groups_workflow_in_starting_stage():
    html = render_entries([workflow()])
    assert 'data-group="research"' in html
    assert 'data-group="workflow"' not in html


def test_build_substitutes_stage_count_and_type_filter():
    html = build([
        asset(stage="research"),
        workflow(id="second-flow", _file="second-flow.yaml", stage="remediate"),
    ])
    assert "2 assets" in html
    assert "Across 2 workflow stages" in html
    assert 'data-type="workflow"' in html
    assert 'data-type="prompt"' in html


def test_stage_count_counts_distinct_stages_present():
    spread = [
        asset(stage="intake-classify"),
        asset(stage="research"),
        asset(stage="remediate"),
        asset(stage="communicate"),
    ]
    assert stage_count(spread) == 4
    # A missing stage drops the count; duplicates do not inflate it.
    assert stage_count([asset(stage="research"), asset(stage="research")]) == 1
    assert stage_count(spread[:3]) == 3


def test_offline_scan_catches_external_src_in_chrome():
    html = '<main id="library"></main><img src="https://example.com/logo.png">'
    assert any("src" in e for e in check_offline(html))


def test_offline_scan_catches_css_import_in_chrome():
    html = '<style>@import url("https://example.com/a.css");</style><main id="library"></main>'
    assert any("@import" in e for e in check_offline(html))


def test_offline_scan_ignores_prompt_prose_storage_and_url_tokens():
    html = build([
        asset(
            body="Mention localStorage, document.cookie, @import, url(https://example.com/a.css), and https://example.com as prose."
        )
    ])
    assert check_offline(html) == []


def test_offline_scan_catches_template_chrome_storage_reference():
    html = '<main id="library"></main><script>localStorage.setItem("x","y")</script>'
    errors = check_offline(html)
    assert any("localStorage" in e for e in errors)

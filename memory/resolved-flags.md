# Resolved flags

This file records security alerts, monitoring flags, and automated scan hits that have been investigated and closed. The daily diff routine and any future monitoring session should check this file before surfacing a flag as active. A flag listed here has been reviewed by Shane and confirmed as a non-issue.

## Format

Each entry carries: the flag as it appeared in the source tool, the source (GitGuardian, Gmail alert, etc.), the date resolved, and the verdict. The verdict field is the one sentence that matters for future suppression.

---

## Entries

### Bearer Token exposure — `generative-ai` repo

| Field | Value |
|---|---|
| Source | GitGuardian (surfaced via Daily Diff email) |
| First flagged | ~2026-05-19 (approximately 38 days before resolution) |
| Resolved | 2026-06-27 |
| Verdict | Non-issue. The repo is a fork of an external project, never live, never Shane's code. The token was present in the forked source, not introduced by Shane and not used in any active deployment. |

**Suppression instruction:** Do not flag GitGuardian Bearer Token alerts originating from the `generative-ai` repo. If a new token exposure surfaces in a different repo or context, treat it as active and flag it normally.

---

## How to use this file

Before including a security or monitoring flag in a diff report:

1. Check if the flag (by repo, tool, and token type) matches an entry here.
2. If it matches and the verdict is non-issue, omit it from the report or note it briefly as "previously resolved — see `memory/resolved-flags.md`."
3. If the same flag reappears in a materially different context (different repo, different token, different deployment), treat it as a new issue and flag it.

New resolved flags should be added here in the same session they are resolved, with a clear verdict and suppression instruction.

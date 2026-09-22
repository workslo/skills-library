---
name: create-a-skill
description: Interview the user and draft an installable SKILL.md for Microsoft 365 Copilot hosts.
---
You help an operator author a custom `SKILL.md` for Microsoft 365 Copilot.

Goal: produce one complete `SKILL.md` that can be installed in the chosen host with no missing sections.

Supported hosts:
- Word
- Excel
- PowerPoint
- Copilot Cowork
- AI in SharePoint

Process:
1. Ask the minimum discovery questions needed to define scope, inputs, outputs, guardrails, and handoff boundaries.
2. Confirm the target host and any host limits that affect structure.
3. Draft the skill in plain markdown with clear, testable instructions.
4. Run the draft against the review checklist and patch gaps.
5. Return the final `SKILL.md` plus install notes for the chosen host.

Always include:
- purpose and operating context
- required inputs and expected output shape
- constraints, exclusions, and safety boundaries
- step-by-step execution instructions
- quality checks before release

When requirements are ambiguous, ask focused follow-up questions before drafting.

Use these companion references while drafting:
- `references/skill-spec.md`
- `references/office-host-guide.md`
- `references/worked-examples.md`
- `references/review-checklist.md`

If the user wants a tenant-native deployment artifact, point them to:
- `assets/declarative-agent-instructions.md`
- `assets/declarative-agent-setup.md`
- `assets/sharepoint-site-context.md`
- `assets/sharepoint-create-a-skill.md`
- `assets/sharepoint-setup.md`

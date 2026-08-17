# Skill specification (host-neutral)

A valid custom skill should include:

1. **Intent** - one sentence that states what task is completed.
2. **Scope** - what is in and out of bounds.
3. **Inputs** - required user inputs and optional context.
4. **Execution steps** - ordered steps that can be followed without guessing.
5. **Output contract** - expected format, fields, and quality checks.
6. **Failure handling** - what to do when inputs are missing or contradictory.
7. **Safety boundaries** - actions to refuse and escalation paths.

Write instructions as direct actions. Prefer short sections over dense prose.

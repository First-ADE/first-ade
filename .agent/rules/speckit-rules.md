---
trigger: always_on
---

## Spec-Kit Context

Before ANY spec-kit workflow (`/speckit.*`), you MUST load and respect:

1. **Constitution**: `.specify/memory/constitution.md` — 7 binding principles with axiom traceability
2. **Templates**: `.specify/templates/` — canonical formats for `spec.md`, `plan.md`, `tasks.md`
3. **Axioms**: `docs/AXIOMS.md` — the 5 foundational truths (Σ.1–Σ.5)
4. **Postulates**: `docs/POSTULATES.md` — three orders of derivations (Π.x.y)

## Constitutional Compliance

- All generated specs, plans, and tasks MUST comply with the constitution's Quality Gates
- The `plan-template.md` Constitution Check gate (§30–34) MUST be filled before Phase 0
- Test-first (Red-Green-Refactor) is NON-NEGOTIABLE per Principle III
- ADRs are REQUIRED for new components, tech selections, and breaking changes per Principle IV

## File References

@.specify/*

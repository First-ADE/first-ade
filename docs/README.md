# ADE Documentation

**Axiom Driven Engineering — Core Documentation Hub**

---

## 📚 Documentation Index

| Document                             | Description                             |
| ------------------------------------ | --------------------------------------- |
| [MANIFESTO.md](./MANIFESTO.md)       | The philosophy and vision of ADE        |
| [AXIOMS.md](./AXIOMS.md)             | The five fundamental axioms (Σ.1–Σ.5)   |
| [POSTULATES.md](./POSTULATES.md)     | Three orders of postulate derivations   |
| [CONSTITUTION.md](./CONSTITUTION.md) | Governance principles and quality gates |
| [METHODOLOGY.md](./METHODOLOGY.md)   | The ADE lifecycle (Specify→Implement)   |

---

## 🏛️ Architecture Decision Records

ADRs document significant architectural decisions with axiom traceability.

| [ADR-0001](./decisions/0001-adopt-axiom-driven-engineering.md) | Adopt Axiom Driven Engineering |
| [ADR-0002](./decisions/0002-test-heuristic-enhancement-and-test-coverage.md) | Test Heuristic Enhancement and Test Coverage |
| [ADR-0003](./decisions/0003-harden-default-quality-gate-strictness-to-enforce.md) | Harden default quality gate strictness to enforce |

See [ADR Guide](./adr-guide.md) for how to write new ADRs.

---

## 🧬 Axiomatic Hierarchy

```
Σ.X     Axioms            ← Fundamental truths (5 core)
  │
  ├─ Π.X.1  First-Order   ← Direct derivations
  │    │
  │    ├─ Π.X.2  Second-Order   ← Practical applications
  │    │    │
  │    │    └─ Π.X.3  Third-Order   ← Implementation patterns
  │
  └─ Constitutional Principles
       │
       └─ Architecture Decision Records
            │
            └─ Implementation
```

---

## 🚀 Quick Start

1. Read [MANIFESTO.md](./MANIFESTO.md) for the "why"
2. Study [AXIOMS.md](./AXIOMS.md) for the foundation
3. Review [METHODOLOGY.md](./METHODOLOGY.md) for the "how"
4. Apply via templates in `../templates/`

---

*Building on first principles, one axiom at a time.*

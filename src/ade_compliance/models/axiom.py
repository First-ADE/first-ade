# implements: FR-007
# traces_to: Π.3.1

"""Domain models for axioms, violations, and traceability links.

Defines the core compliance primitives: axiom rules, violation tracking
with a guarded state machine, and traceability link records.
"""

from . import (
    Axiom,
    InvalidStateTransition,
    Severity,
    TraceLink,
    Violation,
    ViolationState,
)

__all__ = [
    "Axiom",
    "InvalidStateTransition",
    "Severity",
    "TraceLink",
    "Violation",
    "ViolationState",
]

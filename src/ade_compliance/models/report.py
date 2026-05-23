# implements: FR-012
# traces_to: Π.3.1

"""Domain model for the aggregate compliance report.

The ComplianceReport collects violations, traceability matrices, and
metrics from a compliance run into a single serializable document.
"""

from . import ComplianceReport

__all__ = ["ComplianceReport"]

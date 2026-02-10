"""T064: Prometheus-compatible metrics for observability (FR-026).

Exposes counters and histograms for compliance checks, attestations,
violations, escalations, and check duration.
"""

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

# Counters
compliance_checks_total = Counter(
    "compliance_checks_total",
    "Total number of compliance checks run",
)

compliance_violations_total = Counter(
    "compliance_violations_total",
    "Total number of violations detected",
    ["axiom_id", "severity"],
)

attestation_total = Counter(
    "attestation_total",
    "Total number of attestations recorded",
    ["status"],
)

escalation_total = Counter(
    "escalation_total",
    "Total number of escalations triggered",
)

# Histograms
attestation_confidence = Histogram(
    "attestation_confidence",
    "Distribution of attestation confidence scores",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

check_duration_seconds = Histogram(
    "check_duration_seconds",
    "Duration of compliance checks in seconds",
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
)


def get_metrics_output() -> tuple[bytes, str]:
    """Generate Prometheus metrics output.

    Returns:
        Tuple of (metrics_bytes, content_type_string).
    """
    return generate_latest(), CONTENT_TYPE_LATEST

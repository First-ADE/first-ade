# implements: FR-002
# traces_to: Π.2.1

from ade_compliance.observability.metrics import (
    compliance_checks_total,
    get_metrics_output,
)


def test_metrics_output():
    compliance_checks_total.inc()
    data, content_type = get_metrics_output()
    assert b"compliance_checks_total" in data
    assert "text/plain" in content_type

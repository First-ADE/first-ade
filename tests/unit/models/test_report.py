"""T048: Unit tests for ComplianceReport model.

Verifies schema versioning, field naming aliases, backward compatibility property redirects,
and Pydantic serialization characteristics.
"""

from datetime import datetime

from ade_compliance.models.axiom import Violation
from ade_compliance.models.report import ComplianceReport


def test_report_default_values():
    """Verify default values and alias routing in ComplianceReport."""
    report = ComplianceReport(repo_root=".")

    assert report.schema_version == "1.0.0"
    assert report.version == "1.0.0"
    assert isinstance(report.generated_at, datetime)
    assert report.timestamp == report.generated_at
    assert report.repo_root == "."
    assert report.violations == []
    assert report.summary == {}


def test_report_serialization():
    """Verify serialization parses both field names and aliases correctly."""
    violation = Violation(
        axiom_id="Π.1.1",
        file_path="src/main.py",
        message="Missing specification.",
    )
    report = ComplianceReport(
        repo_root=".",
        commit_sha="a1b2c3d4",
        check_duration_ms=120,
        violations=[violation],
        metrics={"coverage": 85.0},
    )

    data = report.model_dump(by_alias=True)
    assert data["version"] == "1.0.0"
    assert "timestamp" in data
    assert data["repo_root"] == "."
    assert data["commit_sha"] == "a1b2c3d4"
    assert data["check_duration_ms"] == 120
    assert len(data["violations"]) == 1
    assert data["metrics"]["coverage"] == 85.0


def test_report_generate_summary():
    """Verify summary calculations match the violations counted."""
    report = ComplianceReport(
        repo_root=".",
        violations=[
            Violation(axiom_id="Π.1.1", file_path="a.py", message="No spec"),
            Violation(axiom_id="Π.2.1", file_path="b.py", message="No test"),
        ],
    )

    summary_text = report.generate_summary()
    assert "Violations: 2" in summary_text
    assert report.summary["total"] == 2
    assert report.summary["new"] == 2
    assert report.summary["resolved"] == 0


def test_report_summary_includes_all_states():
    """Summary should count all four violation states."""
    v_new = Violation(axiom_id="Π.1.1", file_path="a.py", message="A")
    v_ack = Violation(axiom_id="Π.2.1", file_path="b.py", message="B")
    v_ack.acknowledge()
    v_over = Violation(axiom_id="Π.3.1", file_path="c.py", message="C")
    v_over.override()

    report = ComplianceReport(repo_root=".", violations=[v_new, v_ack, v_over])
    report.generate_summary()

    assert report.summary["total"] == 3
    assert report.summary["new"] == 1
    assert report.summary["acknowledged"] == 1
    assert report.summary["resolved"] == 0
    assert report.summary["overridden"] == 1

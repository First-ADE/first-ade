"""T060: Integration tests for HTTP API endpoints.

Tests the FastAPI server endpoints using TestClient.
"""

import pytest
from fastapi.testclient import TestClient

from ade_compliance.server import create_app


@pytest.fixture
def client(tmp_path):
    """Create a test client with a temporary config."""
    app = create_app(config_path=None, audit_path=str(tmp_path / "test_audit.sqlite").replace("\\", "/"))
    return TestClient(app)


class TestHealthEndpoint:
    """T062: Health endpoint tests."""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_status(self, client):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"


class TestCheckEndpoint:
    """T062: Check endpoint tests."""

    def test_check_accepts_files(self, client):
        """POST /check should accept a list of files and return results."""
        response = client.post("/check", json={"files": ["src/ade_compliance/cli.py"]})
        assert response.status_code == 200
        data = response.json()
        assert "violations" in data

    def test_check_empty_files_returns_empty(self, client):
        """POST /check with empty files should return no violations."""
        response = client.post("/check", json={"files": []})
        assert response.status_code == 200
        data = response.json()
        assert data["violations"] == []


class TestAttestEndpoint:
    """T062: Attest endpoint tests."""

    def test_attest_high_confidence(self, client):
        """POST /attest with high confidence should return passed status."""
        response = client.post(
            "/attest",
            json={
                "agent_id": "test-agent",
                "task_id": "T001",
                "confidence": 0.9,
                "axioms_applied": ["S.1"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "passed"
        assert data["agent_id"] == "test-agent"

    def test_attest_low_confidence_escalates(self, client):
        """POST /attest with low confidence should return escalated status."""
        response = client.post(
            "/attest",
            json={
                "agent_id": "test-agent",
                "task_id": "T002",
                "confidence": 0.3,
                "axioms_applied": ["S.1"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "escalated"

    def test_attest_missing_fields_returns_422(self, client):
        """POST /attest with missing required fields should return 422."""
        response = client.post("/attest", json={"agent_id": "test-agent"})
        assert response.status_code == 422


class TestReportsEndpoint:
    """T063: Reports endpoint tests."""

    def test_reports_returns_list(self, client):
        """GET /reports should return a list of audit entries."""
        response = client.get("/reports")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_reports_with_limit(self, client):
        """GET /reports?limit=5 should respect the limit parameter."""
        response = client.get("/reports?limit=5")
        assert response.status_code == 200


class TestOverridesEndpoint:
    """T063: Overrides endpoint tests."""

    def test_overrides_returns_list(self, client):
        """GET /overrides should return a list."""
        response = client.get("/overrides")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestMetricsEndpoint:
    """T064: Prometheus metrics endpoint tests."""

    def test_metrics_returns_200(self, client):
        """GET /metrics should return 200."""
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_returns_prometheus_format(self, client):
        """GET /metrics should return Prometheus text format."""
        response = client.get("/metrics")
        content_type = response.headers.get("content-type", "")
        # Prometheus format is text/plain or openmetrics
        assert "text/plain" in content_type or "text" in content_type

    def test_metrics_contains_expected_counters(self, client):
        """GET /metrics should contain expected metric names."""
        # First trigger some activity
        client.post(
            "/attest",
            json={
                "agent_id": "test-agent",
                "task_id": "T001",
                "confidence": 0.9,
                "axioms_applied": ["S.1"],
            },
        )
        response = client.get("/metrics")
        body = response.text
        assert "attestation_total" in body

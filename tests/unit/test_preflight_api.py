# implements: FR-015
# traces_to: Π.2.1

"""Integration tests for preflight and prompt decorator API endpoints."""

import uuid

from fastapi.testclient import TestClient

from ade_compliance.server import create_app


def test_preflight_api_endpoint(tmp_path):
    """Verify that /api/v1/compliance/preflight correctly returns strictness, target axioms, and file constraints."""
    db_file = tmp_path / f"preflight_{uuid.uuid4().hex[:8]}.sqlite"
    app = create_app(audit_path=str(db_file).replace("\\", "/"))
    client = TestClient(app)

    request_data = {"files": ["src/ade_compliance/services/override.py", "tests/unit/test_config.py"]}

    response = client.post("/api/v1/compliance/preflight", json=request_data)
    assert response.status_code == 200

    res_json = response.json()
    assert res_json["global_strictness"] == "enforce"
    assert res_json["enforce_coverage"] is True
    assert res_json["min_coverage_threshold"] == 80
    assert res_json["traceability_required"] is True

    # Governing axioms
    axioms = res_json["governing_axioms"]
    axiom_ids = [ax["id"] for ax in axioms]
    assert "Π.2.1" in axiom_ids
    assert "Π.3.1" in axiom_ids

    # File constraints
    file_constraints = res_json["file_constraints"]
    assert "src/ade_compliance/services/override.py" in file_constraints
    assert file_constraints["src/ade_compliance/services/override.py"]["is_core"] is True
    assert file_constraints["src/ade_compliance/services/override.py"]["strictness"] == "enforce"

    assert "tests/unit/test_config.py" in file_constraints
    assert file_constraints["tests/unit/test_config.py"]["is_core"] is False
    assert file_constraints["tests/unit/test_config.py"]["strictness"] == "enforce"


def test_prompt_decorate_api_endpoint(tmp_path):
    """Verify that /api/v1/prompts/decorate returns a formatted Markdown response."""
    db_file = tmp_path / f"prompt_dec_{uuid.uuid4().hex[:8]}.sqlite"
    app = create_app(audit_path=str(db_file).replace("\\", "/"))
    client = TestClient(app)

    # Without query parameters
    response = client.get("/api/v1/prompts/decorate")
    assert response.status_code == 200

    res_json = response.json()
    assert "markdown" in res_json
    markdown = res_json["markdown"]
    assert "### First-ADE Compliance Constitution" in markdown
    assert "Global Compliance Mode" in markdown
    assert "Expected Annotation Formatting (Rule Π.3.1)" in markdown

    # With target files in query parameter
    response_files = client.get("/api/v1/prompts/decorate?files=src/ade_compliance/services/override.py")
    assert response_files.status_code == 200
    res_json_files = response_files.json()
    assert "Planned Target File Constraints" in res_json_files["markdown"]
    assert "override.py" in res_json_files["markdown"]

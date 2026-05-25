# implements: FR-015
# traces_to: Π.2.1

"""Unit tests for the prompt decorator utility."""

from ade_compliance.config import Config
from ade_compliance.utils.prompts import generate_prompt_decorator


def test_generate_prompt_decorator_defaults():
    """Verify prompt decorator output matches standard default configuration."""
    config = Config()
    markdown = generate_prompt_decorator(config)

    assert "### First-ADE Compliance Constitution" in markdown
    assert "**Global Compliance Mode**: `ENFORCE`" in markdown
    assert "- **Spec Quality Gate**: `ENABLED` (Strictness: `ENFORCE`)" in markdown
    assert "- **Test Coverage Gate**: `ENABLED` (Strictness: `ENFORCE`, Required Coverage: `80%`)" in markdown
    assert "- **Traceability Annotations Gate**: `ENABLED` (Strictness: `ENFORCE`)" in markdown
    assert "Expected Annotation Formatting (Rule Π.3.1)" in markdown
    assert "# implements: FR-XXX" in markdown
    assert "# traces_to: Π.X.Y" in markdown


def test_generate_prompt_decorator_overrides():
    """Verify prompt decorator includes active axiom overrides and target file limits."""
    config = Config()
    config.global_settings.strictness = "warn"
    config.engines.test.min_coverage = 90
    config.axioms = {
        "Π.2.1": "enforce",
        "Π.3.1": "audit",
    }

    files = ["src/ade_compliance/models/axiom.py", "tests/unit/test_config.py"]
    markdown = generate_prompt_decorator(config, files)

    assert "**Global Compliance Mode**: `WARN`" in markdown
    assert "Required Coverage: `90%`" in markdown
    assert "Specific Axiom Strictness Overrides:" in markdown
    assert "- `Π.2.1`: Overridden strictness to `ENFORCE`" in markdown
    assert "- `Π.3.1`: Overridden strictness to `AUDIT`" in markdown

    assert "Planned Target File Constraints:" in markdown
    assert (
        "- `src/ade_compliance/models/axiom.py`: Core Business Logic: `YES` | Required Strictness: `ENFORCE`"
        in markdown
    )
    assert "- `tests/unit/test_config.py`: Core Business Logic: `NO` | Required Strictness: `WARN`" in markdown

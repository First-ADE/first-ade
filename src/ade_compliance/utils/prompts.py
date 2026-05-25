# implements: FR-018
# traces_to: Π.3.1

"""Prompt decoration utilities for dynamic LLM alignment and self-attestation."""

from typing import List, Optional

from ..config import Config


def generate_prompt_decorator(config: Config, files: Optional[List[str]] = None) -> str:
    """Generate a highly structured Markdown prompt block based on active compliance constraints.

    Args:
        config: Loaded Config instance.
        files: Optional list of target file paths to customize prompts for.

    Returns:
        A Markdown prompt block to be injected into system instructions.
    """
    global_strict = config.global_settings.strictness.upper()

    spec_status = "ENABLED" if config.engines.spec.enabled else "DISABLED"
    spec_strict = config.engines.spec.strictness.upper()

    test_status = "ENABLED" if config.engines.test.enabled else "DISABLED"
    test_strict = config.engines.test.strictness.upper()
    min_cov = config.engines.test.min_coverage or 80

    trace_status = "ENABLED" if config.engines.trace.enabled else "DISABLED"
    trace_strict = config.engines.trace.strictness.upper()

    adr_enabled = getattr(config.engines, "adr", None) is not None and config.engines.adr.enabled
    adr_status = "ENABLED" if adr_enabled else "DISABLED"
    adr_strict = config.engines.adr.strictness.upper() if adr_enabled else "ENFORCE"

    # Specific Axiom Strictness
    axiom_lines = []
    if config.axioms:
        for ax_id, strictness in sorted(config.axioms.items()):
            axiom_lines.append(f"  - `{ax_id}`: Overridden strictness to `{strictness.upper()}`")

    axioms_section = ""
    if axiom_lines:
        axioms_section = "\n#### Specific Axiom Strictness Overrides:\n" + "\n".join(axiom_lines) + "\n"

    # Optional Target File Constraints section
    file_constraints_section = ""
    if files:
        file_constraints_section = "\n#### Planned Target File Constraints:\n"
        for f in files:
            is_core = (
                any(part in f.lower() for part in ["models", "engines", "services", "config", "db"])
                and "tests" not in f.lower()
            )
            strictness = "ENFORCE" if is_core else config.global_settings.strictness.upper()
            file_constraints_section += (
                f"- `{f}`: Core Business Logic: `{'YES' if is_core else 'NO'}` | Required Strictness: `{strictness}`\n"
            )

    markdown_prompt = f"""### First-ADE Compliance Constitution

You are an autonomous AI coding assistant. You must adhere to the following project compliance rules at all times to pass our quality gates:

- **Global Compliance Mode**: `{global_strict}` (Violations will block pipeline runs)

#### Active Verification Gates:
- **Spec Quality Gate**: `{spec_status}` (Strictness: `{spec_strict}`)
- **Test Coverage Gate**: `{test_status}` (Strictness: `{test_strict}`, Required Coverage: `{min_cov}%`)
- **Traceability Annotations Gate**: `{trace_status}` (Strictness: `{trace_strict}`)
- **Architecture Decisions Gate**: `{adr_status}` (Strictness: `{adr_strict}`)

{axioms_section}{file_constraints_section}
#### Expected Annotation Formatting (Rule Π.3.1):
All new and modified source code and test files must contain explicit trace comments at the top linking them to specifications and postulates:
- `# implements: FR-XXX` (where FR-XXX is the Functional Requirement ID)
- `# traces_to: Π.X.Y` (where Π.X.Y is the governing Postulate/Axiom ID)

*Your actions will be statically audited by First-ADE. All generated test suites must be hermetically isolated, deterministic (no network or randomized timing), and core business logic must strictly exceed target thresholds.*
"""
    return markdown_prompt

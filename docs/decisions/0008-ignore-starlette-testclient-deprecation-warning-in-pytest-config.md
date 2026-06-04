# Ignore starlette testclient deprecation warning in pytest config

* Status: accepted
* Deciders: Antigravity Coding Assistant, USER
* Date: 2026-06-03

Technical Story: Resolve CI failures caused by StarletteDeprecationWarning being treated as error during pytest execution in GitHub Actions environment.

## Context and Problem Statement

Our pytest configuration uses `filterwarnings = ["error"]` to treat warnings as errors to maintain high quality. However, package updates on GHA runners introduced `starlette.exceptions.StarletteDeprecationWarning` regarding `httpx` and `starlette.testclient` deprecation. Because this warning triggers during test collection, it blocks the entire test run. How do we resolve this without downgrading starlette or breaking older package compatibility?

## Decision Drivers

*   **CI Stability**: Pull Request checks and tests must pass reliably in the CI environment.
*   **Version Compatibility**: The codebase should work cleanly on developer machines with both older and newer dependency versions.
*   **Warning Hygiene**: We should maintain warning-as-error strictness for our own code while tolerating external library deprecation warnings we cannot control.

## Considered Options

*   **Option 1**: Add message-based warning filters in `pyproject.toml` to ignore deprecation and user warnings matching `.*httpx.*`.
*   **Option 2**: Class-based warning filter ignoring `starlette.exceptions.StarletteDeprecationWarning`. (Rejected: triggers import errors on older starlette versions).
*   **Option 3**: Modify all CI workflow files to run pytest with `-W` command-line flags. (Rejected: duplicates configuration across multiple files).

## Decision Outcome

Chosen option: "Option 1", because message-based filters allow selective exclusion of the Starlette warning across all environments without depending on specific class imports that may not exist in older package versions.

### Positive Consequences

*   Tests pass successfully in both local and CI environments.
*   Keeps warnings-as-errors strictness active for all other potential code issues.

### Negative Consequences

*   Deprecation warnings related to httpx/starlette will be silent.


# Test Heuristic Enhancement and Test Coverage

* Status: approved
* Deciders: Antigravity, USER
* Date: 2026-05-23

Technical Story: Resolve Π.2.1 and Π.3.1 compliance violations for missing tests and false positives.

## Context and Problem Statement

The `TestEngine` used a very rigid candidate mapping heuristic that flagged architectural files as missing tests even when valid unit or integration tests existed under slightly different suffixes (e.g. `_unit.py`) or in nested folders. Furthermore, 16 core files lacked explicit, targeted tests. How do we enhance test mappings to prevent false positives and expand test coverage to 100% compliance?

## Decision Drivers

* Strict compliance with postulate Π.2.1 (Test-first alignment)
* Keep test suite dry and clean without duplicating functional integration assertions
* Comprehensive coverage of utility and model functions

## Considered Options

* **Option 1**: Keep strict candidate list and create duplicate test files mapping to them.
* **Option 2**: Refactor `TestEngine` candidates list to support integration folders, observability subfolders, utility subfolders, and suffixes like `_unit.py`. Additionally, implement distinct tests for completely uncovered files (e.g. `async_helpers.py` and `path.py`).

## Decision Outcome

Chosen option: **Option 2**, because it represents an elegant, dry, and robust architectural refactoring. It enhances search coverage while avoiding duplicate assertions.

### Positive Consequences

* 100% of functional codebase modules are now covered by unit or integration tests under Π.2.1.
* The test execution suite is clean and dry.
* Avoided false-positive compliance warnings.

### Negative Consequences

* Requires updating the compliance engine's file-finding mapping.

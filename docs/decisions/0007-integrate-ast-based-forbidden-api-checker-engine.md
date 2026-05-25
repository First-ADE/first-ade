# Integrate AST-based forbidden API checker engine

* Status: accepted
* Deciders: Antigravity Coding Assistant, USER
* Date: 2026-05-24

Technical Story: Implement AST-based static analysis engine scanning Python test files for forbidden API calls violating test determinism requirements (FR-015, Π.2.2).

## Context and Problem Statement

To satisfy FR-015 and ensure complete test suite determinism, we need an engine to detect and block non-deterministic or externally-dependent API calls (such as `time.sleep()`, unseeded `random` calls, `datetime.now()`, direct HTTP/network calls, or `os.system()`). Doing this via simple regex substring searches is prone to false positives (e.g. flagging comments, docs, or variables). Therefore, we need a robust AST-based static analysis engine.

## Decision Drivers

* **Determinism**: Test suites must run hermetically without timing dependencies, unseeded RNG, or direct network IO.
* **Accuracy**: Static analysis should parse the code AST to avoid false positives on comments or mock definitions.
* **Performance**: AST walk should be fast and non-disruptive.

## Considered Options

* **Option 1**: Add a dedicated `ForbiddenAPIEngine` performing AST walk using Python's `ast` module, checking module and function call nodes.
* **Option 2**: Depend exclusively on external tools or simple substring matches.

## Decision Outcome

Chosen option: "Option 1", because AST-based analysis provides precise detection of actual call nodes and allows tracking from-imports and seeded state cleanly without false positives on mock string literals.

### Positive Consequences

* Robust detection of timing, RNG, and I/O violations in tests.
* Easy configuration and inclusion in the standard compliance check pipeline.

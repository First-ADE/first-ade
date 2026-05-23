# Harden compliance validation path standardisation and concurrency

* Status: accepted
* Deciders: Antigravity Coding Assistant, USER
* Date: 2026-05-23

Technical Story: Resolution of Spec Audit issues #55-#63 and 10 codebase quality gaps.

## Context and Problem Statement

To prevent bypasses of the test-first and traceability engines when files are passed as absolute paths or relative paths with `./`, we must standardise all path checking. We must also secure override creation against malformed/empty scopes which could disable checks globally, optimize database connection overhead, and serialize concurrent checks per-file to satisfy FR-030.

## Decision Drivers

* **Security**: Malformed override scopes must not globally disable checks.
* **Accuracy**: Path representation differences must not allow verification bypasses.
* **Performance**: Redundant SQLAlchemy metadata table creations and connections must be cached.
* **Concurrency**: Concurrent checks must be serialized per-file without race conditions in the audit logs.

## Considered Options

* **Option 1**: Implement centralized path normalization, scope type/value validation on overrides, connection pool session caching, and standard cross-platform file-system locking.
* **Option 2**: Implement these changes in an ad-hoc manner in the individual engines without centralization.

## Decision Outcome

Chosen option: "Option 1", because it establishes clean, centralized helpers (`normalize_project_path` and `file_system_lock`) and robust thread-safe caches, adhering strictly to Constitutional Principle V (Architectural Constraints) and Principle VII (Coverage and gates).

### Positive Consequences

* Robust path validation guarantees that test-first and traceability validation can never be bypassed using path variants.
* Malformed overrides are actively blocked before being saved.
* Concurrent file checks are safely serialized cross-platform.
* Sub-millisecond database connection and transaction speeds.

## Pros and Cons of the Options

### Option 1 (Centralized & Hardened)

* Good, because it provides robust, standard library based path sanitization and cross-platform file locking.
* Good, because it caches SQLite engines thread-safely.
* Bad, because it adds slight complexity to the orchestrator execution path.

### Option 2 (Ad-hoc)

* Good, because it requires fewer codebase files modified initially.
* Bad, because it risks path representation drift and duplication of database creation code.


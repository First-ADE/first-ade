# Refactor service layer with OOP singleton and custom exceptions

* Status: accepted
* Deciders: Antigravity Coding Assistant, USER
* Date: 2026-05-23

Technical Story: Comprehensive OOP and Pythonic refactoring of First-ADE services and connection handling.

## Context and Problem Statement

To transition First-ADE from procedural connection management and generic exception raising into a state-of-the-art Pythonic OOP structure, we must encapsulate SQLAlchemy session management inside a thread-safe singleton, create a standardized base class for services, and establish a custom domain exception tree that implements multiple inheritance for complete backward compatibility.

## Decision Drivers

* **Clean Boundaries**: Services should inherit from a unified base class and avoid duplicate connection initialization code.
* **Test Isolation**: Singleton database engines must not bleed data across concurrent pytest runs.
* **Error Semantics**: Replace generic built-in exception raising (like ValueError or RuntimeError) with rich, domain-relevant exception classes.
* **Modern Python Features**: Utilize Python 3.10+ features like structural pattern matching (`match/case`) and `typing.Self` for clean control flow and expressiveness.

## Considered Options

* **Option 1**: Implement a thread-safe `DatabaseManager` singleton scoped by config instances, a unified `BaseService` with lazy dependency resolution, custom multi-inheritance exceptions (inheriting from both domain exceptions and standard built-ins), and pattern matching subcommand routing in the CLI.
* **Option 2**: Maintain the current procedural database helper functions and generic built-in exceptions.

## Decision Outcome

Chosen option: "Option 1", because it enforces strict OOP design cohesion, provides robust error semantics, and satisfies all BDD/ADR requirements while ensuring 100% backward compatibility with all existing tests.

### Positive Consequences

* Clean, unified service boundary structure through the `BaseService` abstraction.
* Complete thread safety and zero metadata initialization overhead on real database connections.
* Seamless test isolation via configuration-scoped connection caches.
* Downstream callers can cleanly catch domain exceptions or standard built-in types seamlessly.

## Pros and Cons of the Options

### Option 1 (OOP & Pythonic Refactoring)

* Good, because it reduces boilerplate service connection setup.
* Good, because it makes error catching highly precise via custom exceptions.
* Good, because it implements modern Python `match/case` for subcommand routing and exit code maps.
* Bad, because it introduces multiple inheritance in exceptions which requires careful design.

### Option 2 (Keep Procedural)

* Good, because it requires zero architectural changes or new files.
* Bad, because it retains boilerplate database code in all service constructors and lacks precise domain exceptions.

# FR-001: Greeter

## Requirement

`greet(name)` returns the string `"Hello, <name>."` for any non-empty name and raises `ValueError` for an empty one.

## Acceptance

```gherkin
Feature: Greeting
  Scenario: A named caller is greeted
    Given the name "Ada"
    When greet is called
    Then the result is "Hello, Ada."

  Scenario: An empty name is refused
    Given the name ""
    When greet is called
    Then a ValueError is raised
```

## Traceability

Implemented by `src/greeter.py` (marker `implements: FR-001`). Verified by `tests/test_greeter.py`.

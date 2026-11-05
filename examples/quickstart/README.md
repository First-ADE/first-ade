# Quickstart: ADE in five minutes

Two tiny projects, one function each. `pass/` is what Axiom-Driven Engineering asks for; `fail/` is the same function with the discipline removed. The compliance CLI accepts one and refuses the other, and you can watch exactly why.

## Run it

From the repository root, with Python 3.11+ and [uv](https://docs.astral.sh/uv/) installed:

```bash
uv sync --extra dev

cd examples/quickstart/pass
uv run --project ../../.. ade-compliance check-all src tests
echo "exit: $?"        # 0

cd ../fail
uv run --project ../../.. ade-compliance check-all src tests
echo "exit: $?"        # 1
```

On Windows PowerShell the same commands work; use `$LASTEXITCODE` for the exit code.

## What you will see

The CLI writes one JSON audit event per line. The last one is `RUN_COMPLETE` with `violations_count`.

`pass/` reports `"violations_count": 0` and exits 0, because:

| What is there | Which postulate it satisfies |
| --- | --- |
| `specs/FR-001-greeter.md` states the requirement and its acceptance scenarios | Π.1.1 a specification exists |
| `tests/test_greeter.py` exists for `src/greeter.py` | Π.2.1 every source module has a test |
| `src/greeter.py` opens with `# implements: FR-001` and `# traces_to: …` | Π.3.1 code declares what it implements |
| the test uses no wall clock, network or shell | Π.2.2 tests are deterministic |

`fail/` reports `"violations_count": 4` and exits 1, with one `VIOLATION_DETECTED` event each:

| Event | Why |
| --- | --- |
| `Π.1.1` at `.` | no `specs/` directory, so nothing says what `greet` is supposed to do |
| `Π.2.1` at `src/greeter.py` | no `tests/test_greeter.py` |
| `Π.3.1` at `src/greeter.py` | no `implements:` / `traces_to:` marker, so the code cannot be traced to a requirement |
| `Π.2.2` at `tests/test_clock.py`, severity critical | the test calls `datetime.datetime.now()`; its result depends on when it runs |

## What this is and is not

The engines here are deliberately simple: the spec engine looks for `specs/**/*.md` relative to the working directory, the test engine looks for `tests/test_<module>.py` beside `src/`, the trace engine reads comment markers, and the forbidden-API engine scans test files for a fixed list of non-deterministic calls. That is enough to make the idea concrete: a property you care about becomes a check, and the check runs before the code is accepted. The full postulate set is in [`../../docs/POSTULATES.md`](../../docs/POSTULATES.md).

Both runs also append to a local `.ade_compliance/audit.sqlite`, a hash-chained audit log; it is ignored by git.

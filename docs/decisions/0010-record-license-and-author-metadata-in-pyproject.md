# Record License and Author Metadata in Pyproject

* Status: accepted
* Deciders: Brandon Fox
* Date: 2026-11-06

Technical Story: The project ships with a LICENSE file and a CITATION.cff but `pyproject.toml` carried no `license` or `authors` fields, so the package metadata did not say who holds the copyright or under what terms the code may be used.

## Context and Problem Statement

A published Python package carries its own metadata. Without `license` and `authors` in `pyproject.toml`, tooling such as PyPI, `pip show` and SBOM generators report the package as unlicensed and unattributed, even though the repository root says MIT and names the author. Postulate Π.3.1 treats `pyproject.toml` as an architectural file, so the change is recorded here.

## Decision Drivers

*   **Honest metadata**: what the package says about itself must match the LICENSE file and CITATION.cff in the repository.
*   **Personal capacity**: the author line names the individual, not any employer, consistent with the Independence section of the README.
*   **Minimal change**: two fields, no build or runtime behaviour altered.

## Considered Options

*   **Option 1**: Add `license = { text = "MIT" }` and one `authors` entry to `[project]` in `pyproject.toml`.
*   **Option 2**: Leave `pyproject.toml` unchanged and rely on the LICENSE file alone.
*   **Option 3**: Use the PEP 639 `license = "MIT"` string form with `license-files`.

## Decision Outcome

Chosen option: "Option 1", because it is the form the current build backend and the pinned packaging tools already accept, and it makes the package metadata agree with the repository without touching the build.

### Positive Consequences

*   `pip show ade-compliance` and generated SBOMs report MIT and the author.
*   The package metadata, LICENSE and CITATION.cff all name the same holder.

### Negative Consequences

*   The table form of `license` is deprecated by PEP 639; a later ADR can move to the string form once the build backend is upgraded.

## Pros and Cons of the Options

### Option 1: Table form in `[project]`

*   Good, because it is accepted by the current toolchain without changes.
*   Bad, because PEP 639 deprecates the table form.

### Option 2: LICENSE file only

*   Good, because nothing changes.
*   Bad, because installed metadata stays silent about license and author.

### Option 3: PEP 639 string form

*   Good, because it is the current standard.
*   Bad, because it needs a newer build backend than the one pinned today.

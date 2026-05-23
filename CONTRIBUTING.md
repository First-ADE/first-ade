# Contributing to First-ADE

Welcome! We are excited to have you contribute to the ADE Compliance Framework. To maintain our high standards of architectural excellence, security, and velocity, we adhere to strict contribution guidelines.

---

## 📐 Pull Request Rules & Guidelines

To keep our codebase healthy, maintain high review quality, and prevent regression, all Pull Requests (PRs) must adhere to the following constraints:

### 1. Keep PRs Small and Focused
- **Size Limit**: Pull Requests should ideally be around **200 lines of changes** or fewer. Small, concise PRs are easier to review, minimize regression risks, and can be integrated rapidly.
- **Single Responsibility**: Each PR must address a single task, feature, or bug fix. Avoid bundling unrelated refactorings or changes.

### 2. Passing CI Checks and Tests
- **Pre-Review Readiness**: Before a PR is considered ready for review, it **must pass all automated CI checks and tests** successfully. Reviewers will not audit PRs with failing pipeline runs.
- **Warning Enforcement**: In accordance with our compliance gates, all tests must pass with **zero warnings** or deprecation notifications.

### 3. Independence and Compatibility
- **No Merge Conflicts**: PRs must be clean, fully rebased, and synchronized with the target branch. Resolve all merge conflicts locally before requesting a review.
- **No Overlapping Issues**: PRs should not introduce new, unresolved requirements or conflict with already open PRs. Ensure your changes operate in isolation without contaminating ongoing developer streams.

---

## 🛠️ Local Development & Verification

Before submitting your PR, execute the compliance verification pipeline locally:

### 1. Code Quality & Formatting
Run linting and strict type checking to ensure clean compilation:
```powershell
uv run ruff check .
uv run mypy src/
```

### 2. Test Execution
Verify the complete test suite runs successfully with **zero warnings**:
```powershell
uv run pytest
```

### 3. Compliance Framework Gate
Execute the automated compliance orchestrator against your local changes:
```powershell
ade-compliance check-all src/
```

Thank you for helping us maintain absolute compliance and engineering excellence!

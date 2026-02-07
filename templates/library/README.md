# {{project_name}}

> *Built with Axiom Driven Engineering*

## 🎯 Overview

A brief description of what this library does.

## 📦 Installation

```bash
uv pip install {{project_name}}
```

## 🚀 Quick Start

```python
from {{project_name}} import example

result = example.do_something()
```

## 📐 Axiom Alignment

This project follows [Axiom Driven Engineering](https://github.com/First-ADE) principles:

- **Σ.1**: Specifications in `.specify/specs/`
- **Σ.2**: Tests verify all behavior
- **Σ.3**: ADRs in `docs/decisions/`
- **Σ.5**: AI context in `.gemini.md`, `.claude.md`

## 🛠️ Development

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for package management

### Setup

```bash
# Clone the repository
git clone https://github.com/First-ADE/{{project_name}}.git
cd {{project_name}}

# Create virtual environment and install dependencies
uv venv
uv pip install -e ".[dev]"
```

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov={{project_name}}
```

### Linting

```bash
ruff check .
mypy src/
```

## 📖 Documentation

- [API Reference](./docs/api.md)
- [Architecture Decision Records](./docs/decisions/)
- [Specifications](./specs/)

## 🤝 Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## 📜 License

MIT License - see [LICENSE](./LICENSE) for details.

---

*Building on first principles, one axiom at a time.*

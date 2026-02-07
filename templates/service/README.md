# {{service_name}}

> *Serverless Service — Built with Axiom Driven Engineering*

## 🎯 Overview

{{service_description}}

## 🏗️ Architecture

```
src/
├── main.py          # Cloud Run entrypoint
├── routes/          # API route handlers
├── services/        # Business logic
├── models/          # Data models
└── utils/           # Utility functions
```

## 🚀 Deployment

### Prerequisites

- Google Cloud SDK
- Docker
- [uv](https://docs.astral.sh/uv/) for package management

### Local Development

```bash
# Install dependencies
uv venv
uv pip install -e ".[dev]"

# Run locally
python -m src.main

# Or with Docker
docker build -t {{service_name}} .
docker run -p 8080:8080 {{service_name}}
```

### Deploy to Cloud Run

```bash
gcloud run deploy {{service_name}} \
    --source . \
    --region {{region}} \
    --allow-unauthenticated
```

## 📐 Axiom Alignment

This service follows [ADE principles](https://github.com/First-ADE):

| Axiom   | Implementation                 |
| ------- | ------------------------------ |
| **Σ.1** | Specs in `.specify/specs/`     |
| **Σ.2** | pytest + integration tests     |
| **Σ.3** | ADRs in `docs/decisions/`      |
| **Σ.4** | Route → Service → Model layers |
| **Σ.5** | AI context in `.gemini.md`     |

## 🧪 Testing

```bash
# Unit tests
pytest tests/unit

# Integration tests
pytest tests/integration

# All tests with coverage
pytest --cov=src
```

## 📖 API Documentation

See [API Reference](./docs/api.md) for endpoint documentation.

## 🔐 Environment Variables

| Variable | Description                    | Required           |
| -------- | ------------------------------ | ------------------ |
| `PORT`   | Server port                    | No (default: 8080) |
| `ENV`    | Environment (dev/staging/prod) | No                 |

## 🤝 Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

---

*Building on first principles, one axiom at a time.*

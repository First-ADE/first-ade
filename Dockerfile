# Multi-stage build for ultra-small, secure production image
# Stage 1: Build virtual environment and dependencies using astral-sh/uv
FROM python:3.11-slim-bookworm AS builder

# Install uv
COPY --from=astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy only the files needed for dependency installation
COPY pyproject.toml uv.lock ./

# Create virtualenv and install project dependencies (without the package itself)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv /opt/venv && \
    uv pip install --no-install-project -r pyproject.toml

# Copy source and template files
COPY src ./src
COPY templates ./templates
COPY alembic.ini ./

# Install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --no-deps .

# Stage 2: Final minimal production image
FROM python:3.11-slim-bookworm AS runner

WORKDIR /app

# Copy virtual environment and packages from builder stage
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

# Set PATH to use the virtual environment binaries directly
ENV PATH="/opt/venv/bin:$PATH"

# Run as non-root user for security hardening
RUN useradd -u 10001 -m appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose default port (Cloud Run standard)
EXPOSE 8080

# Configure uvicorn entrypoint (Fail-closed single-worker REST API)
ENTRYPOINT ["uvicorn", "ade_compliance.server:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]

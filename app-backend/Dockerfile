FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.10 /uv /uvx /bin/

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --extra dev --frozen --no-install-project

# Copy application code
COPY . .

# Install project itself
RUN uv sync --extra dev --frozen

# Environment variables
ENV PYTHONPATH=/app

# Default command (overridden by docker-compose)
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

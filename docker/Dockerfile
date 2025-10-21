FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Copy project files
COPY pyproject.toml poetry.lock* ./
COPY src/ ./src/
COPY config/ ./config/

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

# Create non-root user
RUN useradd -m -u 1000 paperless && \
    chown -R paperless:paperless /app && \
    mkdir -p /app/logs /app/data && \
    chown -R paperless:paperless /app/logs /app/data

USER paperless

# Expose ports
EXPOSE 8080 9090

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s \
  CMD python -c "import sys; sys.exit(0)"

# Run application
CMD ["python", "-m", "better_paperless", "--help"]
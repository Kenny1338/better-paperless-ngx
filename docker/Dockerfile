FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.2

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Configure Poetry to not create virtual environments and install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi --no-root

# Copy project files
COPY src/ ./src/
COPY config/ ./config/

# Install the project itself
RUN poetry install --only-root --no-interaction --no-ansi

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
CMD ["python", "-m", "better_paperless", "batch"]
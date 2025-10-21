FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install Poetry and export requirements
RUN pip install poetry && \
    poetry export -f requirements.txt --output requirements.txt --without-hashes && \
    pip install -r requirements.txt && \
    pip uninstall -y poetry

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Install the package
RUN pip install -e .

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
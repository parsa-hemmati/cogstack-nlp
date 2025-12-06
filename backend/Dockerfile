# Clinical Care Tools - Backend Dockerfile
# Base image: Python 3.11 slim (security-hardened)
FROM python:3.11-slim-bookworm

# Metadata
LABEL maintainer="clinical-care-tools@example.com"
LABEL description="Clinical Care Tools Backend API (FastAPI)"
LABEL version="0.1.0"

# Security: Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    postgresql-client \
    # WeasyPrint dependencies for PDF export
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libcairo2 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip==24.3.1 \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app ./app
COPY ./alembic ./alembic
COPY ./alembic.ini .
COPY ./pytest.ini .

# Create directories for logs and data (with proper permissions)
RUN mkdir -p /app/logs /app/data \
    && chown -R appuser:appuser /app

# Security: Switch to non-root user
USER appuser

# Expose port 8000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Default command: Run with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

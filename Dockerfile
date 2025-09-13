# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (include tzdata for timezone support)
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Default timezone (can be overridden by TZ env at runtime)
ENV TZ=UTC

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY webhook.py .
COPY webhook_config.py .
COPY auto_reply_config.py .
COPY auto_reply_service.py .
COPY supabase_client.py .
COPY catalog_repository.py .
COPY wa_service.py .
COPY embeddings.py .
COPY orchestrator.py .
COPY session_manager.py .
COPY supabase_schema.sql .
COPY seed_supabase_services.py .
COPY version_info.py .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run the application
CMD ["python", "webhook.py"]

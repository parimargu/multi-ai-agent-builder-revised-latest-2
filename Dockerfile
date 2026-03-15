# ---- Build Stage ----
FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Entrypoint
ENTRYPOINT ["./entrypoint.sh"]

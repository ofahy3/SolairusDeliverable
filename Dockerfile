# Dockerfile for Solairus Intelligence Report Generator

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN adduser --disabled-password --gecos '' --uid 1000 appuser

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY solairus_intelligence/ ./solairus_intelligence/
COPY .env.example .env.example
COPY README.md README.md

# Create output directory with proper ownership
RUN mkdir -p /mnt/user-data/outputs && chown -R appuser:appuser /mnt/user-data/outputs

# Set ownership of app directory
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8080

# Run the application
CMD exec uvicorn solairus_intelligence.web.app:app --host 0.0.0.0 --port ${PORT}

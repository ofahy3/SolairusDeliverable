# Dockerfile for MRO Intelligence Report Generator

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
COPY mro_intelligence/ ./mro_intelligence/
COPY .env.example .env.example

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
CMD exec uvicorn mro_intelligence.web.app:app --host 0.0.0.0 --port ${PORT}

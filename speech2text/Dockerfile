# CPU-only Dockerfile for Google CloudRun deployment with pre-built models
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    wget \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install uv

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt ./
RUN uv pip install --system -r requirements.txt

# Set up model cache directory (persistent location)
ENV HF_HOME=/app/models
ENV TRANSFORMERS_CACHE=/app/models
ENV HF_DATASETS_CACHE=/app/models
RUN mkdir -p /app/models

# Pre-download Kyutai STT models during build
# This adds ~2.4GB to the image but ensures fast startup
COPY download_models.py /tmp/download_models.py
RUN echo "Pre-downloading Kyutai STT models..." && \
    python /tmp/download_models.py && \
    rm /tmp/download_models.py

# Copy application code
COPY . .

# Set environment variables for CloudRun
ENV PORT=8080
ENV HOST=0.0.0.0
ENV PYTHONPATH=/app

# Create a simple health check endpoint
EXPOSE 8080

# Default command for CPU-only deployment
CMD ["python", "proper_moshi_server.py"]
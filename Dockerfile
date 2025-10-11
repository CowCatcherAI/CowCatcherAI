FROM python:3.11-slim

LABEL maintainer="CowCatcher AI"
LABEL description="CowCatcher AI - Automated cow heat detection system"

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY cowcatcher/ ./cowcatcher/
COPY webui/ ./webui/

# Copy startup script
COPY startup.sh .
RUN chmod +x startup.sh

# Create data directory for persistent storage
RUN mkdir -p /app/data

# Expose web UI port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health', timeout=5)" || exit 1

# Run startup script
CMD ["/bin/bash", "/app/startup.sh"]

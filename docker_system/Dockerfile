# Dockerfile for PO Processing System
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY scripts/ ./

# Create directories
RUN mkdir -p /app/input /app/processed /app/archive /app/errors

# Set permissions
RUN chmod +x *.py

# Set the TESSDATA_PREFIX environment variable
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata/

# Run the file monitor
CMD ["python", "nas_folder_monitor.py", "/app/input", "/app/processed", "/app/archive", "/app/errors"]
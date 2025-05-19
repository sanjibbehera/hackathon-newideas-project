# Stage 1: Base image with Python
FROM python:3.9-slim as base

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Stage 2: Runtime image
FROM python:3.9-slim

WORKDIR /app

# Copy from base stage
COPY --from=base /app /app
COPY --from=base /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Install ChromaDB dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgomp1 && \
    rm -rf /var/lib/apt/lists/*

# Create data directory
RUN mkdir -p /app/data/aws_errors && \
    mkdir -p /app/data/aws_rag_db

# Download Ollama (if needed)
RUN curl -L https://ollama.ai/download/ollama-linux-amd64 -o /usr/bin/ollama && \
    chmod +x /usr/bin/ollama

# Initialize RAG DB and start services
CMD ["sh", "-c", "ollama serve & python -c 'from app.services.aws_error_service import AWSErrorService; AWSErrorService()' && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Upgrade pip (important for wheels)
RUN pip install --upgrade pip

# Copy the lightweight production requirements first for Docker layer caching.
# The image intentionally excludes torch/transformers/sentence-transformers/
# faiss-cpu/spacy so the runtime stays far below Render Free's 512 MB limit.
COPY requirements-prod.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy backend code (see .dockerignore for excluded dev/user artifacts)
COPY . .

EXPOSE 10000

# Render injects $PORT; default to 10000 for local runs.
# Single uvicorn process, no worker duplication.
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]



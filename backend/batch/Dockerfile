FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/api:/app

WORKDIR /app

COPY backend/pyproject.toml /app/pyproject.toml
RUN pip install --upgrade pip && pip install -e .[jobs,ai]

COPY backend/api /app/api
COPY backend/core /app/core
COPY backend/batch /app/batch
COPY backend/db /app/db

ENTRYPOINT ["python", "-m", "batch.app"]

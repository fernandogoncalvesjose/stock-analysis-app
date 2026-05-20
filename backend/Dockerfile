FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/backend/api:/app/backend

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY backend/requirements.txt /app/backend/requirements.txt

FROM base AS development
RUN pip install --upgrade pip && pip install -r /app/backend/requirements.txt
COPY backend /app/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--app-dir", "backend/api", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS production
RUN pip install --upgrade pip && pip install -r /app/backend/requirements.txt
COPY backend /app/backend
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--app-dir", "backend/api", "--host", "0.0.0.0", "--port", "8000"]

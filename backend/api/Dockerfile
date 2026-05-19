FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY backend/pyproject.toml /app/pyproject.toml
RUN pip install --upgrade pip && pip install -e .

COPY backend/api /app/api
COPY backend/core /app/core
COPY backend/db /app/db

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--app-dir", "api", "--host", "0.0.0.0", "--port", "8000"]

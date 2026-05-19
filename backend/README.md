# Stock Analysis Backend

Backend FastAPI modular, async e preparado para producao.

## Stack

- FastAPI + Pydantic v2
- SQLAlchemy 2.0 async + asyncpg
- Alembic
- PostgreSQL
- Repository pattern + services + DTOs
- Batch noturno preparado para APScheduler/GitHub Actions
- Extensoes para IA em processamento batch

## Local

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev,jobs,ai]
copy ..\.env.example .env
alembic upgrade head
uvicorn app.main:app --app-dir api --reload --port 8000
```

Healthcheck:

```http
GET http://localhost:8000/api/v1/health
```

## Batch

```bash
python -m batch.app --reference-date 2026-05-19
```

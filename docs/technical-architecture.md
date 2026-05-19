# Arquitetura Técnica
# Plataforma de Análise de Ações — Production-Ready

| Campo | Valor |
|-------|-------|
| **Versão** | 1.0 |
| **Status** | Rascunho |
| **Última atualização** | 19/05/2026 |
| **Documento base** | [prd.md](./prd.md) |
| **Responsável** | Engenharia |

---

## Índice

1. [Arquitetura Geral](#1-arquitetura-geral)
2. [Fluxo Completo de Dados](#2-fluxo-completo-de-dados)
3. [Estrutura Completa de Pastas](#3-estrutura-completa-de-pastas)
4. [Arquitetura do Backend](#4-arquitetura-do-backend)
5. [Estratégia de Processamento Noturno](#5-estratégia-de-processamento-noturno)
6. [Estratégia de IA](#6-estratégia-de-ia)
7. [Estratégia de Banco de Dados](#7-estratégia-de-banco-de-dados)
8. [Estratégia de APIs Externas](#8-estratégia-de-apis-externas)
9. [Estratégia de Frontend](#9-estratégia-de-frontend)
10. [Estratégia de Autenticação Futura](#10-estratégia-de-autenticação-futura)
11. [Estratégia de Observabilidade](#11-estratégia-de-observabilidade)
12. [Estratégia de Deploy](#12-estratégia-de-deploy)
13. [Estratégia de Ambiente Local](#13-estratégia-de-ambiente-local)
14. [Estratégia Docker](#14-estratégia-docker)
15. [Roadmap Técnico do MVP](#15-roadmap-técnico-do-mvp)
16. [Riscos Técnicos e Mitigação](#16-riscos-técnicos-e-mitigação)
17. [Design Patterns Recomendados](#17-design-patterns-recomendados)
18. [Estratégia de Crescimento Futuro](#18-estratégia-de-crescimento-futuro)

---

## Princípios Arquiteturais

| # | Princípio | Implicação |
|---|-----------|------------|
| P1 | **Math decides; AI explains** | `RecommendationEngine` é código puro; LLM nunca altera scores |
| P2 | **Read path ≠ Write path** | Usuário lê snapshot; batch escreve staging → domínio → snapshot |
| P3 | **Um query por página** | `stock_analysis_snapshot` desnormalizado |
| P4 | **Sem IA em tempo real no MVP** | Zero chamadas OpenAI no request HTTP do usuário |
| P5 | **Idempotência em batch** | Reprocessar o mesmo `reference_date` produz o mesmo resultado |
| P6 | **Modular monolith** | Um repositório, pacotes Python isolados, deploy separado por artefato |

### Stack Oficial

| Camada | Tecnologia | Versão mínima |
|--------|------------|---------------|
| Frontend | Next.js + TypeScript | 15.x |
| UI | Tailwind CSS + shadcn/ui | — |
| API | FastAPI + Pydantic | Python 3.12+ |
| Banco | PostgreSQL (Supabase) | 15+ |
| ORM / migrations | SQLAlchemy 2 + Alembic | — |
| Cache | Redis (Upstash) | Opcional MVP; recomendado pós-500 DAU |
| Jobs | APScheduler + GitHub Actions Cron | — |
| IA | OpenAI API (`gpt-4o-mini`) | Batch only |
| Deploy | Vercel + Supabase | — |

---

## 1. Arquitetura Geral

### 1.1 Diagrama de Contexto (C4 — Nível 1)

```mermaid
flowchart TB
    subgraph users [Usuários]
        U[Investidor Web]
    end

    subgraph vercel [Vercel]
        WEB[Next.js 15 App]
        EDGE[Edge Middleware]
        BFF[Route Handlers / Server Actions]
    end

    subgraph compute [Computação Python]
        API[FastAPI - Read API]
        WORKER[Batch Worker + APScheduler]
    end

    subgraph data [Dados]
        PG[(Supabase PostgreSQL)]
        REDIS[(Upstash Redis)]
        STORAGE[Supabase Storage]
    end

    subgraph external [Externos - apenas batch]
        YF[Yahoo Finance / yfinance]
        NEWS[News API / RSS]
        OAI[OpenAI API]
    end

    subgraph ops [Operações]
        GHA[GitHub Actions Cron]
        SENTRY[Sentry]
    end

    U --> WEB
    WEB --> EDGE
    EDGE --> BFF
    BFF --> API
    BFF -.->|opcional leitura direta| PG
    API --> PG
    API --> REDIS
    GHA --> WORKER
    WORKER --> PG
    WORKER --> REDIS
    WORKER --> YF
    WORKER --> NEWS
    WORKER --> OAI
    WORKER --> STORAGE
    WEB --> SENTRY
    API --> SENTRY
    WORKER --> SENTRY
```

### 1.2 Responsabilidades por Camada

| Componente | Responsabilidade | O que NÃO faz |
|------------|------------------|---------------|
| **Next.js (frontend)** | UI, SSR/ISR, SEO, BFF fino, cache HTTP | Regra de scoring, chamadas a Yahoo/OpenAI |
| **FastAPI (backend/api)** | API REST read-only, validação, rate limit, cache Redis | Processamento batch, escrita massiva |
| **backend/core** | Domínio: scoring, normalização, validação IA | HTTP, SQL direto |
| **backend/batch** | Ingestão, pipeline noturno, publicação | Atender usuário |
| **Supabase PostgreSQL** | Source of truth, snapshots, histórico | Lógica de negócio |
| **Redis** | Cache de resposta, rate limit, dedupe LLM | Persistência primária |
| **APScheduler / GHA** | Disparo e orquestração temporal | — |
| **OpenAI** | Narrativas batch | Recomendação BUY/HOLD/SELL |

### 1.3 Topologia de Deploy (MVP — Baixo Custo)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              PRODUÇÃO                                    │
├─────────────────────────────────────────────────────────────────────────┤
│  Vercel          →  frontend (Next.js 15)                               │
│                     - ISR ranking: revalidate 86400                      │
│                     - SSR stock detail                                   │
│                     - Rewrites /api/* → FastAPI (opcional)             │
├─────────────────────────────────────────────────────────────────────────┤
│  Fly.io / Railway →  backend/api (FastAPI)  OU  api.*.vercel.app       │
│                     - 1-2 instâncias pequenas, autoscale leitura         │
├─────────────────────────────────────────────────────────────────────────┤
│  GitHub Actions  →  backend/batch (cron 02:00 BRT)                         │
│                     - Container job com timeout 4h                       │
│                     - Secrets: DATABASE_URL, OPENAI_API_KEY             │
├─────────────────────────────────────────────────────────────────────────┤
│  Supabase        →  PostgreSQL + connection pooler (6543)               │
│                     - RLS desabilitado no MVP (service role no server)   │
├─────────────────────────────────────────────────────────────────────────┤
│  Upstash         →  Redis serverless (cache + rate limit)              │
└─────────────────────────────────────────────────────────────────────────┘
```

**Decisão MVP — caminho de leitura (escolher uma):**

| Opção | Prós | Contras | Quando usar |
|-------|------|---------|-------------|
| **A) Next.js → FastAPI → PG** | Contrato API claro, rate limit centralizado | +1 hop de rede | Time full-stack Python |
| **B) Next.js Server Component → Supabase (service role)** | Menor latência, menos infra | Lógica SQL no TS ou RPC | Maximizar velocidade/custo |
| **Recomendado MVP** | **Híbrido:** ranking/home via ISR + snapshot RPC; busca e feedback via FastAPI | — | Melhor dos dois |

### 1.4 Boundaries de Serviços (Lógicos)

Não são microserviços no MVP — são **módulos deployáveis**:

| Artefato | Runtime | Porta / Trigger |
|----------|---------|-----------------|
| `frontend` | Node (Vercel) | HTTPS 443 |
| `backend/api` | Uvicorn (Fly/Railway) | 8000 |
| `backend/batch` | Python CLI / Docker | Cron / manual |
| `backend/core` | Biblioteca | Import only |

---

## 2. Fluxo Completo de Dados

### 2.1 Visão End-to-End

```mermaid
sequenceDiagram
    participant Cron as Cron (GHA/APScheduler)
    participant Batch as Batch Worker
    participant YF as Yahoo Finance
    participant News as News Provider
    participant Core as backend/core
    participant OAI as OpenAI
    participant PG as PostgreSQL
    participant Redis as Redis
    participant API as FastAPI
    participant Web as Next.js
    participant User as Usuário

    Note over Cron,PG: JANELA NOTURNA (02:00-06:00 BRT)

    Cron->>Batch: run_pipeline(reference_date)
    Batch->>PG: sync_tickers (universo B3 ativo)
    Batch->>YF: fetch quotes + fundamentals
    YF-->>Batch: raw payloads
    Batch->>PG: upsert stock_metrics_daily
    Batch->>Core: normalize + compute scores
    Core-->>Batch: scores + recommendation
    Batch->>PG: upsert stock_scores_daily
    Batch->>News: fetch articles (7d window)
    News-->>Batch: articles + sentiment (rule-based)
    Batch->>PG: upsert stock_news
    Batch->>OAI: narratives (changed scores only)
    OAI-->>Batch: text + token usage
    Batch->>Core: validate narratives
    Batch->>PG: publish snapshots + ranking
    Batch->>Redis: invalidate keys snapshot:*
    Batch->>PG: batch_job_runs SUCCESS

    Note over Web,User: CAMINHO DIURNO (leitura)

    User->>Web: GET /stock/ITUB4
    Web->>API: GET /api/v1/stocks/ITUB4
    API->>Redis: GET snapshot:ITUB4:2026-05-19
    alt cache hit
        Redis-->>API: JSON
    else cache miss
        API->>PG: SELECT snapshot WHERE ticker, date
        PG-->>API: row
        API->>Redis: SETEX 3600
    end
    API-->>Web: StockSnapshotDTO
    Web-->>User: HTML + hydrated sections
```

### 2.2 Etapas Detalhadas

> **Referência:** horários `+00:xx` são offsets relativos ao início do pipeline. Em produção o pipeline inicia às **02:00 BRT** (mesmos offsets: 02:00, 02:10, …).

| +00:xx | BRT (prod) | Job | Descrição resumida |
|--------|------------|-----|-------------------|
| 00:00 | 02:00 | `sync_tickers` | Atualizar universo de tickers B3 ativos |
| 00:10 | 02:10 | `ingest_metrics` | Preços, volume, fundamentos → `stock_metrics_daily` |
| 00:20 | 02:20 | `compute_scores` | Sub-scores, composto, recomendação, flags de risco |
| 00:30 | 02:30 | `ingest_news` | Notícias 7d + sentiment (regras) → `stock_news` |
| 00:40 | 02:40 | `generate_ai_narratives` | Textos IA (batch) com validação |
| 00:50 | 02:50 | `publish_snapshots` | Snapshot, ranking, cache, encerramento do job |

**Duração alvo:** ~50–60 min (núcleo). Janela máxima com buffer e retries: **02:00–06:00 BRT**.

#### Fase 1 — Universo de tickers (`sync_tickers`) · 00:00

| Entrada | Processamento | Saída |
|---------|---------------|-------|
| Lista B3 (fonte estática + validação) | Filtrar liquidez/market cap mínimos | `stocks` (upsert, `is_active`) |
| Tickers novos/removidos | Log de diff para auditoria | `batch_job_steps.metadata` |

#### Fase 2 — Métricas (`ingest_metrics`) · 00:10

Combina mercado + fundamentos no mesmo slot (internamente: `ingest_market_data` + `ingest_fundamentals`).

| Entrada | Processamento | Saída |
|---------|---------------|-------|
| `stocks` ativos | Chunk 50 tickers; rate limit Yahoo | `provider_cache` (JSON bruto, TTL 24h) |
| Tickers B3 | Normalizar símbolo `.SA` para yfinance | `stock_metrics_daily` |
| Histórico OHLCV 2y | Calcular SMA, RSI offline | campos técnicos no JSONB `metrics` |

```text
ingest_raw_market       → provider_cache
ingest_raw_fundamentals → provider_cache
normalize               → stock_metrics_daily (reference_date, ticker, metrics JSONB)
```

#### Fase 3 — Scores (`compute_scores`) · 00:20

```text
stock_metrics_daily
    → MetricNormalizer (percentil setorial)
    → FundamentalScorer | DividendScorer | TechnicalScorer
    → CompositeScorer (pesos de scoring_config)
    → RecommendationEngine → BUY | HOLD | SELL
    → RiskRuleEngine → flags[] (métricas; sem notícias)
    → stock_scores_daily
```

**Importante:** `RecommendationEngine` vive em `backend/core/scoring/recommendation.py` — sem import de OpenAI. Notícias **não** entram no score numérico.

#### Fase 4 — Notícias (`ingest_news`) · 00:30

| Etapa | Detalhe |
|-------|---------|
| Fonte primária MVP | RSS agregado + Yahoo Finance news endpoint |
| Dedupe | Hash `sha256(source_url)` |
| Vínculo ticker | Match por ticker no título/tags |
| Sentiment | `RuleSentimentAnalyzer` (sem LLM) → `stock_news.sentiment` |
| Flags extras | `NEGATIVE_NEWS_CLUSTER` pode alimentar narrativa de riscos na publicação |
| Limite | 5 artigos/ticker/7 dias no snapshot |

#### Fase 5 — Análise IA (`generate_ai_narratives`) · 00:40

| Campo gerado | Input LLM | Validador |
|--------------|-----------|-----------|
| `company_summary` | Fatos estruturados + sector | max 150 palavras |
| `recommendation_explanation` | `score_breakdown` JSON | deve citar ≥3 componentes; não contradizer recommendation |
| `risk_narrative` | `risks[]` flags (+ notícias se flag) | sem novos riscos |
| `news_summary` (opcional) | título + lead do artigo | sem fatos novos |

**Gate de custo:** só chama OpenAI se `abs(score_delta) >= 5` ou `narrative_missing`.

#### Fase 6 — Publicação (`publish_snapshots`) · 00:50

```sql
-- Transação única por reference_date
BEGIN;
  -- 1. Montar JSON snapshot por ticker
  INSERT INTO stock_analysis_snapshot (...) 
  ON CONFLICT (ticker, reference_date) DO UPDATE ...;
  
  -- 2. Ranking atômico
  DELETE FROM ranking_dividends_daily WHERE reference_date = :d;
  INSERT INTO ranking_dividends_daily SELECT ... ORDER BY dividend_rank_score DESC LIMIT 20;
  
  -- 3. Marcar job
  UPDATE batch_job_runs SET status = 'SUCCESS', finished_at = now() WHERE id = :id;
COMMIT;
```

#### Fase 7 — Consumo Frontend

| Página | Estratégia | Fonte de dados |
|--------|------------|----------------|
| `/` | SSR + cache 1h | ranking preview (top 5) + search index |
| `/stock/[ticker]` | SSR snapshot | `GET /api/v1/stocks/{ticker}` |
| `/ranking/dividends` | ISR `revalidate: 86400` | `GET /api/v1/rankings/dividends` |

---

## 3. Estrutura Completa de Pastas

### 3.1 Monorepo (raiz)

```text
stock-analysis-app/
├── frontend/                                   # Next.js 15 + TypeScript
├── backend/
│   ├── api/                                    # FastAPI (leitura)
│   ├── core/                                   # Domínio Python compartilhado
│   ├── batch/                                  # Pipeline noturno
│   └── db/
│       ├── migrations/                         # Alembic
│       ├── seeds/
│       └── supabase/                           # RLS policies (futuro)
├── infra/
│   ├── docker/
│   └── github/workflows/
├── docs/
│   ├── prd.md
│   └── technical-architecture.md
├── scripts/
│   ├── dev.sh
│   └── seed-local.sh
├── docker-compose.yml
├── docker-compose.prod.yml
├── backend/pyproject.toml                      # workspace Python (uv/poetry)
├── frontend/package.json
├── pnpm-workspace.yaml
├── .env.example
└── README.md
```

### 3.2 Frontend — `frontend/`

```text
frontend/
├── app/
│   ├── layout.tsx                              # fonts, metadata base, providers
│   ├── page.tsx                                # Home (SSR)
│   ├── loading.tsx
│   ├── error.tsx
│   ├── not-found.tsx
│   ├── stock/
│   │   └── [ticker]/
│   │       ├── page.tsx                        # SSR snapshot
│   │       ├── loading.tsx
│   │       └── opengraph-image.tsx             # SEO OG dinâmico
│   ├── ranking/
│   │   └── dividends/
│   │       └── page.tsx                        # ISR
│   ├── about/
│   │   └── page.tsx
│   └── api/                                    # BFF opcional (proxy)
│       └── revalidate/
│           └── route.ts                        # webhook pós-batch (secret)
├── components/
│   ├── ui/                                     # shadcn
│   ├── layout/
│   │   ├── header.tsx
│   │   ├── footer.tsx
│   │   └── disclaimer-banner.tsx
│   ├── search/
│   │   ├── search-bar.tsx                      # Client: debounce
│   │   └── search-results.tsx
│   ├── stock/
│   │   ├── recommendation-badge.tsx
│   │   ├── score-breakdown-chart.tsx           # Client: recharts
│   │   ├── fundamental-section.tsx
│   │   ├── dividend-section.tsx
│   │   ├── technical-section.tsx
│   │   ├── indicators-table.tsx
│   │   ├── company-summary.tsx
│   │   ├── risks-section.tsx
│   │   ├── news-list.tsx
│   │   └── ai-explanation.tsx
│   └── ranking/
│       ├── dividend-ranking-table.tsx
│       └── ranking-row.tsx
├── lib/
│   ├── api/
│   │   ├── client.ts                           # fetch wrapper + types
│   │   ├── stocks.ts
│   │   └── rankings.ts
│   ├── cache/
│   │   └── tags.ts                             # revalidateTag constants
│   ├── utils/
│   │   ├── ticker.ts                           # validate B3 ticker
│   │   └── format.ts                           # números, datas pt-BR
│   └── constants.ts
├── types/
│   ├── stock-snapshot.ts                       # espelha StockSnapshotDTO
│   └── ranking.ts
├── hooks/
│   ├── use-debounced-search.ts
│   └── use-recent-tickers.ts                   # localStorage
├── styles/
│   └── globals.css
├── public/
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── .env.local.example
└── package.json
```

### 3.3 API — `backend/api/`

```text
backend/api/
├── app/
│   ├── main.py                                 # FastAPI factory
│   ├── config.py                               # pydantic-settings
│   ├── dependencies.py                         # DI: db session, redis
│   ├── middleware/
│   │   ├── request_id.py
│   │   ├── rate_limit.py
│   │   └── cors.py
│   ├── api/
│   │   └── v1/
│   │       ├── router.py
│   │       ├── stocks.py
│   │       ├── rankings.py
│   │       ├── health.py
│   │       └── feedback.py
│   ├── schemas/                                # DTOs (Pydantic response)
│   │   ├── stock_snapshot.py
│   │   ├── search.py
│   │   └── ranking.py
│   ├── services/                               # Application services
│   │   ├── stock_read_service.py
│   │   ├── ranking_read_service.py
│   │   └── feedback_service.py
│   ├── repositories/                           # Data access
│   │   ├── stock_snapshot_repository.py
│   │   ├── stock_search_repository.py
│   │   └── ranking_repository.py
│   ├── mappers/
│   │   └── snapshot_mapper.py                # ORM row → DTO
│   └── db/
│       ├── session.py
│       └── models/                             # SQLAlchemy entities (read)
│           ├── stock.py
│           └── snapshot.py
├── tests/
│   ├── api/
│   └── integration/
├── Dockerfile
├── pyproject.toml
└── .env.example
```

### 3.4 Domínio — `backend/core/`

```text
backend/core/
├── src/
│   └── stock_analysis/
│       ├── domain/                             # Entidades + regras puras
│       │   ├── entities/
│       │   │   ├── stock.py
│       │   │   ├── metrics.py
│       │   │   ├── scores.py
│       │   │   └── recommendation.py
│       │   ├── value_objects/
│       │   │   ├── ticker.py
│       │   │   └── money.py
│       │   └── enums/
│       │       ├── recommendation.py           # BUY, HOLD, SELL
│       │       └── risk_flag.py
│       ├── scoring/
│       │   ├── fundamental_scorer.py
│       │   ├── dividend_scorer.py
│       │   ├── technical_scorer.py
│       │   ├── composite_scorer.py
│       │   ├── recommendation_engine.py
│       │   └── risk_rule_engine.py
│       ├── normalization/
│       │   └── metric_normalizer.py
│       ├── sentiment/                          # rule-based MVP
│       │   └── rule_sentiment_analyzer.py
│       ├── ai/
│       │   ├── narrative_generator.py
│       │   ├── validators/
│       │   │   ├── narrative_validator.py
│       │   │   └── schema_validator.py
│       │   └── prompts/
│       │       ├── v1/
│       │       │   ├── recommendation_explanation.yaml
│       │       │   ├── company_summary.yaml
│       │       │   └── risk_narrative.yaml
│       │       └── registry.py
│       ├── ingestion/
│       │   ├── ports/                          # interfaces
│       │   │   ├── market_data_port.py
│       │   │   ├── fundamentals_port.py
│       │   │   └── news_port.py
│       │   └── adapters/
│       │       ├── yahoo_finance_adapter.py
│       │       ├── brapi_adapter.py            # fallback BR
│       │       └── rss_news_adapter.py
│       ├── publishing/
│       │   └── snapshot_builder.py
│       └── common/
│           ├── clock.py
│           └── result.py                       # Result[T, E] pattern
├── tests/
│   ├── scoring/                                # golden tests
│   ├── ai/
│   └── fixtures/
├── pyproject.toml
└── README.md
```

### 3.5 Batch — `backend/batch/`

```text
backend/batch/
├── src/
│   └── batch/
│       ├── __main__.py                         # CLI entry
│       ├── scheduler.py                        # APScheduler (local/dev)
│       ├── orchestrator/
│       │   ├── pipeline.py                     # run_pipeline()
│       │   └── context.py                      # PipelineContext
│       ├── jobs/
│       │   ├── sync_tickers.py              # 00:00 — universo B3
│       │   ├── ingest_metrics.py            # 00:10 — mercado + fundamentos
│       │   ├── compute_scores.py            # 00:20 — scores e recomendação
│       │   ├── ingest_news.py               # 00:30 — notícias + sentiment
│       │   ├── generate_ai_narratives.py    # 00:40 — textos IA
│       │   ├── publish_snapshots.py         # 00:50 — snapshot + ranking + cache
│       │   └── weekly_full_refresh.py       # domingo — backfill
│       ├── jobs/internal/                   # sub-tarefas de ingest_metrics
│       │   ├── ingest_market_data.py
│       │   └── ingest_fundamentals.py
│       ├── infrastructure/
│       │   ├── db/
│       │   │   ├── unit_of_work.py
│       │   │   └── repositories/               # write repos
│       │   ├── redis/
│       │   │   └── cache_invalidator.py
│       │   └── logging/
│       │       └── structured_logger.py
│       └── config.py
├── tests/
├── Dockerfile
└── pyproject.toml
```

### 3.6 Visão do `backend/`

| Subpasta | Deploy | Descrição |
|----------|--------|-----------|
| `backend/api/` | Fly.io / Railway | API REST read-only |
| `backend/core/` | Biblioteca (import) | Domínio, scoring, ingestion, IA |
| `backend/batch/` | GitHub Actions / Cron | Pipeline noturno |
| `backend/db/` | Supabase | Migrations e seeds |

**Workspace Python:** `backend/pyproject.toml` na raiz do backend com membros `api`, `core` e `batch` (uv/poetry workspace).

---

## 4. Arquitetura do Backend

### 4.1 Camadas (Clean / Hexagonal simplificado)

```text
┌──────────────────────────────────────────────────────────────┐
│  Delivery (FastAPI routers / Batch CLI)                       │
├──────────────────────────────────────────────────────────────┤
│  Application Services (orquestração, transações, cache)     │
├──────────────────────────────────────────────────────────────┤
│  Domain (backend/core) — ZERO dependências externas          │
├──────────────────────────────────────────────────────────────┤
│  Infrastructure (repositories, adapters, Redis, OpenAI client) │
└──────────────────────────────────────────────────────────────┘
```

**Regra de dependência:** `domain` ← `application` ← `delivery/infrastructure`. Adapters implementam `ports`.

### 4.2 Módulos e Responsabilidades

| Camada | Artefato | Responsabilidade |
|--------|----------|------------------|
| **Domain** | `entities/`, `scoring/` | Regras de negócio puras |
| **Application** | `backend/api/app/services/*_service.py` | Casos de uso, cache, transação |
| **Repositories** | `*_repository.py` | SQL/ORM, sem lógica de score |
| **DTOs** | `schemas/` (API), `domain` entities | Contrato HTTP; não vazar ORM |
| **Entities (ORM)** | `db/models/` | Mapeamento tabela ↔ Python |
| **Providers** | `ingestion/adapters/` | Yahoo, RSS, OpenAI |
| **Jobs** | `backend/batch/jobs/` | Orquestração temporal |

### 4.3 DTOs Principais (API Response)

```python
# backend/api/app/schemas/stock_snapshot.py (contrato estável)

class RecommendationDTO(str, Enum):
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"

class ScoreBreakdownDTO(BaseModel):
    fundamental: SubScoreDTO
    dividend: SubScoreDTO
    technical: SubScoreDTO
    composite: float

class StockSnapshotDTO(BaseModel):
    ticker: str
    company_name: str
    reference_date: date
    recommendation: RecommendationDTO
    scores: ScoreBreakdownDTO
    fundamentals: FundamentalSectionDTO
    dividends: DividendSectionDTO
    technical: TechnicalSectionDTO
    indicators: list[IndicatorDTO]
    company_summary: str
    risks: RiskSectionDTO
    news: list[NewsItemDTO]
    ai_explanation: str
    data_freshness: DataFreshnessDTO
    scoring_version: str
    disclaimer: str = Field(default=DISCLAIMER_PT)
```

### 4.4 Domain Entity — Recommendation (exemplo)

```python
# backend/core/.../recommendation_engine.py

@dataclass(frozen=True)
class RecommendationResult:
    value: Recommendation  # BUY | HOLD | SELL
    composite_score: Decimal
    config_version: str

class RecommendationEngine:
    def compute(self, composite: Decimal, config: ScoringConfig) -> RecommendationResult:
        if composite >= config.buy_threshold:
            return RecommendationResult(Recommendation.BUY, composite, config.version)
        if composite >= config.hold_threshold:
            return RecommendationResult(Recommendation.HOLD, composite, config.version)
        return RecommendationResult(Recommendation.SELL, composite, config.version)
```

### 4.5 Repository Pattern (leitura)

```python
class StockSnapshotRepository:
    async def get_latest(self, ticker: str) -> StockAnalysisSnapshot | None: ...
    async def get_by_date(self, ticker: str, ref_date: date) -> StockAnalysisSnapshot | None: ...

class StockSearchRepository:
    async def search(self, query: str, limit: int = 10) -> list[StockSearchHit]: ...
    # Usa índice GIN/trigram em stocks.ticker + stocks.name
```

### 4.6 Unit of Work (escrita batch)

```python
class UnitOfWork:
    async def __aenter__(self): ...
    async def __aexit__(self, *exc):
        if exc: await self.rollback()
        else: await self.commit()
    
    @property
    def metrics(self) -> MetricsRepository: ...
    @property
    def scores(self) -> ScoresRepository: ...
    @property
    def snapshots(self) -> SnapshotRepository: ...
```

---

## 5. Estratégia de Processamento Noturno

### 5.1 Ordem dos Jobs (pipeline DAG)

Alinhado ao fluxo noturno em slots de **~10 minutos** (relativo ao `T0` = início do pipeline):

```text
+00:00 (T0)     sync_tickers              # buscar / atualizar tickers
+00:10          ingest_metrics            # mercado + fundamentos → métricas
+00:20          compute_scores            # scores, recomendação, riscos (métricas)
+00:30          ingest_news               # notícias + sentiment (regras)
+00:40          generate_ai_narratives    # análises IA (batch, gate de custo)
+00:50          publish_snapshots         # salvar snapshot, ranking, invalidar cache
```

**Produção (BRT):** `T0 = 02:00` → pipeline núcleo termina ~**02:50**; buffer até 06:00 para retries e universo grande.

| Job | Depende de | Pode falhar parcialmente? |
|-----|------------|---------------------------|
| `sync_tickers` | — | Não (usa lista anterior se falhar) |
| `ingest_metrics` | tickers | Sim (por ticker) |
| `compute_scores` | métricas | Sim (por ticker) |
| `ingest_news` | tickers | Sim (por ticker) |
| `generate_ai_narratives` | scores | Sim (fallback template) |
| `publish_snapshots` | scores | Não (crítico; mantém D-1 se falhar) |

**Domingo 01:00:** `weekly_full_refresh` — backfill 90 dias, recalcula percentis setoriais (fora do DAG diário).

### 5.2 Orquestração

| Ambiente | Mecanismo |
|----------|-----------|
| **Produção** | GitHub Actions `workflow_dispatch` + `schedule: '0 5 * * *'` (UTC = 02:00 BRT) |
| **Staging** | Mesmo workflow, `reference_date` manual |
| **Local** | `APScheduler` em `backend/batch/scheduler.py` ou `python -m batch --job publish_snapshots` |
| **Recovery** | Re-run job individual idempotente |

```python
# backend/batch/src/batch/orchestrator/pipeline.py

PIPELINE_STEPS = [
    ("sync_tickers", sync_tickers.run),                    # +00:00
    ("ingest_metrics", ingest_metrics.run),              # +00:10
    ("compute_scores", compute_scores.run),              # +00:20
    ("ingest_news", ingest_news.run),                    # +00:30 (+ sentiment)
    ("generate_ai_narratives", generate_ai_narratives.run),  # +00:40
    ("publish_snapshots", publish_snapshots.run),        # +00:50 (+ cache)
]

async def run_pipeline(reference_date: date, *, resume_from: str | None = None):
    run_id = await batch_job_runs.start(reference_date)
    for name, fn in PIPELINE_STEPS:
        if resume_from and name != resume_from:
            continue
        await run_step(run_id, name, fn, reference_date)
```

### 5.3 Retries

| Tipo de falha | Política |
|---------------|----------|
| HTTP 429/5xx (Yahoo, News) | Exponential backoff: 2s, 8s, 32s; max 5 tentativas |
| Timeout por ticker | Log + skip ticker; não aborta pipeline inteiro |
| OpenAI rate limit | Batch menor (10 tickers); retry após 60s |
| Falha em `publish_snapshots` | **Crítico** — alerta Pager/email; dia anterior permanece servido |
| Falha parcial ingest | Continua com tickers OK; `data_coverage_pct` no snapshot |

```python
@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, max=60))
async def fetch_with_retry(adapter, ticker): ...
```

### 5.4 Idempotência

| Recurso | Chave de idempotência |
|---------|----------------------|
| `stock_metrics_daily` | `(ticker, reference_date, metric_version)` |
| `stock_scores_daily` | `(ticker, reference_date, scoring_config_version)` |
| `stock_analysis_snapshot` | `(ticker, reference_date)` UPSERT |
| `provider_cache` | `(provider, cache_key)` |
| `ai_narratives` | `(ticker, reference_date, prompt_version, model)` |
| `batch_job_runs` | `(job_name, reference_date)` status não sobrescreve SUCCESS sem `--force` |

### 5.5 Tolerância a Falhas

```text
┌─────────────────────────────────────────────────────────┐
│  Degradação em produção                                  │
├─────────────────────────────────────────────────────────┤
│  Batch falhou hoje → servir snapshot de D-1 + banner     │
│  IA falhou → template estático com bullets dos scores    │
│  Notícias vazias → seção oculta, não erro 500            │
│  Ticker novo sem dados → 404 com sugestões de busca      │
│  <50% métricas → sub-score null + badge "dados parciais" │
└─────────────────────────────────────────────────────────┘
```

### 5.6 Controle de Concorrência

- **Chunk size:** 50 tickers por worker async (`asyncio.gather` com `Semaphore(10)`)
- **Lock distribuído (opcional):** Redis `SET batch:lock:{date} NX EX 14400` evita overlap GHA
- **Timeout global pipeline:** 3h30m hard stop

---

## 6. Estratégia de IA

### 6.1 Onde Usar IA

| Caso de uso | Momento | Modelo | Input |
|-------------|---------|--------|-------|
| Explicação da recomendação | Batch +00:40 (02:40 BRT) | `gpt-4o-mini` | `score_breakdown` JSON |
| Resumo da empresa | Batch (semanal ou delta) | `gpt-4o-mini` | fatos estruturados |
| Narrativa de riscos | Batch | `gpt-4o-mini` | `risks[]` flags |
| Resumo de notícia (opcional) | Batch | `gpt-4o-mini` | título + 300 chars |

### 6.2 Onde NÃO Usar IA

| Proibido | Motivo |
|----------|--------|
| Calcular BUY/HOLD/SELL | RN-01 PRD |
| Normalizar métricas / percentis | Determinístico |
| Sentiment MVP em produção crítica | Usar regras + léxico; LLM sentiment só Fase 2 |
| Busca / autocomplete | PostgreSQL trigram |
| Request HTTP do usuário (MVP) | Latência + custo + alucinação |
| Ranking order | SQL + fórmula fixa |

### 6.3 Versionamento de Prompts

```text
backend/core/.../prompts/
├── registry.py              # prompt_id → loader
├── v1/
│   ├── recommendation_explanation.yaml
│   └── metadata.yaml        # model, max_tokens, temperature=0.2
└── v2/                       # nova versão sem quebrar v1
```

```yaml
# recommendation_explanation.yaml
id: recommendation_explanation
version: "1.0.0"
model: gpt-4o-mini
temperature: 0.2
max_tokens: 400
system: |
  Você explica scores quantitativos para investidores de varejo brasileiros.
  NUNCA altere a recomendação. NUNCA invente números.
user_template: |
  Explique em português a recomendação {{ recommendation }}.
  JSON: {{ score_payload | tojson }}
```

**Persistência:** `ai_narratives.prompt_version` + `prompt_hash` (sha256 do YAML compilado).

### 6.4 Validação Pós-LLM

```python
class NarrativeValidator:
    def validate(self, narrative: str, payload: ScorePayload) -> ValidationResult:
        checks = [
            self._mentions_recommendation(narrative, payload.recommendation),
            self._no_contradiction(narrative, payload.recommendation),
            self._min_score_components_cited(narrative, payload, min_refs=3),
            self._no_invented_numbers(narrative, payload),
        ]
        return ValidationResult(all(checks), checks)
```

Falha → fallback template Jinja2 sem LLM.

### 6.5 Cache e Redução de Custo

| Técnica | Economia estimada |
|---------|-------------------|
| Só regenerar se `|Δscore| >= 5` | ~70% chamadas |
| `prompt_hash` + `payload_hash` em Redis 7d | dedupe replay |
| Batch 20 tickers/request (Responses API) | overhead menor |
| `gpt-4o-mini` + `max_tokens` rígido | $/1M tokens baixo |
| Sem streaming | simplifica |
| Log `tokens_in/out` em `ai_narratives` | finops |

**Meta MVP:** < US$ 50/mês @ 400 tickers.

---

## 7. Estratégia de Banco de Dados

### 7.1 Diagrama ER (simplificado)

```mermaid
erDiagram
    stocks ||--o{ stock_metrics_daily : has
    stocks ||--o{ stock_scores_daily : has
    stocks ||--o{ stock_news : has
    stocks ||--o{ stock_analysis_snapshot : has
    stocks ||--o{ ai_narratives : has
    scoring_config ||--o{ stock_scores_daily : version
    batch_job_runs ||--o{ batch_job_steps : contains
    ranking_dividends_daily }o--|| stocks : lists

    stocks {
        uuid id PK
        string ticker UK
        string name
        string sector
        string isin
        boolean is_active
    }

    stock_analysis_snapshot {
        uuid id PK
        string ticker FK
        date reference_date
        jsonb payload
        string recommendation
        float composite_score
    }
```

### 7.2 DDL Principal (PostgreSQL)

```sql
-- Extensões
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Mestre
CREATE TABLE stocks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticker          VARCHAR(10) NOT NULL UNIQUE,
    name            VARCHAR(255) NOT NULL,
    sector          VARCHAR(100),
    segment         VARCHAR(100),
    isin            VARCHAR(12),
    listing_segment VARCHAR(20),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_stocks_ticker_trgm ON stocks USING gin (ticker gin_trgm_ops);
CREATE INDEX idx_stocks_name_trgm ON stocks USING gin (name gin_trgm_ops);
CREATE INDEX idx_stocks_sector ON stocks (sector) WHERE is_active;

-- Configuração de scoring (versionada)
CREATE TABLE scoring_config (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version         VARCHAR(20) NOT NULL UNIQUE,
    weights         JSONB NOT NULL,          -- {fundamental:0.45, dividend:0.35, technical:0.20}
    thresholds      JSONB NOT NULL,          -- {buy:70, hold:45}
    is_active       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Cache de provedores externos
CREATE TABLE provider_cache (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider        VARCHAR(50) NOT NULL,
    cache_key       VARCHAR(255) NOT NULL,
    payload         JSONB NOT NULL,
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at      TIMESTAMPTZ NOT NULL,
    UNIQUE (provider, cache_key)
);
CREATE INDEX idx_provider_cache_expires ON provider_cache (expires_at);

-- Métricas diárias (histórico)
CREATE TABLE stock_metrics_daily (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stock_id        UUID NOT NULL REFERENCES stocks(id),
    reference_date  DATE NOT NULL,
    metrics         JSONB NOT NULL,          -- normalizadas + raw
    data_coverage   NUMERIC(5,2),            -- 0-100%
    source          VARCHAR(50) NOT NULL DEFAULT 'yahoo',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (stock_id, reference_date)
);
CREATE INDEX idx_metrics_date ON stock_metrics_daily (reference_date);

-- Scores diários (histórico temporal)
CREATE TABLE stock_scores_daily (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stock_id                UUID NOT NULL REFERENCES stocks(id),
    reference_date          DATE NOT NULL,
    fundamental_score       NUMERIC(5,2),
    dividend_score          NUMERIC(5,2),
    technical_score         NUMERIC(5,2),
    dividend_safety_score   NUMERIC(5,2),
    composite_score         NUMERIC(5,2) NOT NULL,
    dividend_rank_score     NUMERIC(5,2),
    recommendation          VARCHAR(4) NOT NULL CHECK (recommendation IN ('BUY','HOLD','SELL')),
    risk_flags              JSONB NOT NULL DEFAULT '[]',
    scoring_config_version  VARCHAR(20) NOT NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (stock_id, reference_date)
);
CREATE INDEX idx_scores_rec_date ON stock_scores_daily (reference_date, recommendation);
CREATE INDEX idx_scores_composite ON stock_scores_daily (reference_date, composite_score DESC);

-- Snapshot desnormalizado (read model)
CREATE TABLE stock_analysis_snapshot (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stock_id            UUID NOT NULL REFERENCES stocks(id),
    ticker              VARCHAR(10) NOT NULL,
    reference_date      DATE NOT NULL,
    payload             JSONB NOT NULL,      -- StockSnapshotDTO completo
    recommendation      VARCHAR(4) NOT NULL,
    composite_score     NUMERIC(5,2) NOT NULL,
    scoring_version     VARCHAR(20) NOT NULL,
    published_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (ticker, reference_date)
);
CREATE INDEX idx_snapshot_ticker_latest ON stock_analysis_snapshot (ticker, reference_date DESC);

-- Notícias
CREATE TABLE stock_news (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stock_id        UUID NOT NULL REFERENCES stocks(id),
    reference_date  DATE NOT NULL,
    title           VARCHAR(500) NOT NULL,
    source_url      TEXT NOT NULL,
    source_name     VARCHAR(100),
    published_at    TIMESTAMPTZ,
    summary         TEXT,
    url_hash        VARCHAR(64) NOT NULL UNIQUE,
    sentiment       VARCHAR(20),             -- POSITIVE | NEUTRAL | NEGATIVE
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_news_stock_date ON stock_news (stock_id, published_at DESC);

-- Narrativas IA
CREATE TABLE ai_narratives (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stock_id        UUID NOT NULL REFERENCES stocks(id),
    reference_date  DATE NOT NULL,
    narrative_type  VARCHAR(50) NOT NULL,    -- recommendation_explanation | company_summary | ...
    content         TEXT NOT NULL,
    prompt_version  VARCHAR(20) NOT NULL,
    prompt_hash     VARCHAR(64) NOT NULL,
    model           VARCHAR(50) NOT NULL,
    tokens_in       INT,
    tokens_out      INT,
    payload_hash    VARCHAR(64) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (stock_id, reference_date, narrative_type, prompt_version)
);

-- Ranking diário
CREATE TABLE ranking_dividends_daily (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reference_date      DATE NOT NULL,
    rank_position       INT NOT NULL,
    stock_id            UUID NOT NULL REFERENCES stocks(id),
    ticker              VARCHAR(10) NOT NULL,
    dividend_rank_score NUMERIC(5,2) NOT NULL,
    dividend_yield      NUMERIC(8,4),
    recommendation      VARCHAR(4) NOT NULL,
    rank_change         INT,                 -- vs dia anterior
    snapshot            JSONB NOT NULL,
    UNIQUE (reference_date, rank_position),
    UNIQUE (reference_date, stock_id)
);
CREATE INDEX idx_ranking_date ON ranking_dividends_daily (reference_date, rank_position);

-- Auditoria batch
CREATE TABLE batch_job_runs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_name        VARCHAR(100) NOT NULL,
    reference_date  DATE NOT NULL,
    status          VARCHAR(20) NOT NULL,    -- RUNNING | SUCCESS | FAILED | PARTIAL
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at     TIMESTAMPTZ,
    rows_affected   INT,
    error_message   TEXT,
    metadata        JSONB
);
CREATE INDEX idx_batch_runs_date ON batch_job_runs (reference_date DESC);

CREATE TABLE batch_job_steps (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id          UUID NOT NULL REFERENCES batch_job_runs(id) ON DELETE CASCADE,
    step_name       VARCHAR(100) NOT NULL,
    status          VARCHAR(20) NOT NULL,
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    error_message   TEXT
);

-- Feedback (MVP opcional)
CREATE TABLE explanation_feedback (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticker          VARCHAR(10) NOT NULL,
    reference_date  DATE NOT NULL,
    is_helpful      BOOLEAN NOT NULL,
    ip_hash         VARCHAR(64),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 7.3 Histórico Temporal

| Tabela | Retenção MVP | Retenção produção |
|--------|--------------|-------------------|
| `stock_metrics_daily` | 2 anos | 5 anos (partition por ano) |
| `stock_scores_daily` | 2 anos | 5 anos |
| `stock_analysis_snapshot` | 90 dias detalhado | 1 ano; depois agregar mensal |
| `provider_cache` | TTL 24–72h | purge job diário |
| `stock_news` | 30 dias | 90 dias |
| `ai_narratives` | 1 ano | 2 anos (auditoria) |

**Particionamento (Fase 2):** `stock_metrics_daily` e `stock_scores_daily` por `RANGE (reference_date)`.

### 7.4 Índices e Performance

| Query pattern | Índice |
|---------------|--------|
| Snapshot por ticker | `(ticker, reference_date DESC)` UNIQUE |
| Último snapshot global | `published_at DESC` (parcial) |
| Busca texto | GIN trigram em `stocks` |
| Ranking do dia | `(reference_date, rank_position)` |
| Job status hoje | `(reference_date, status)` |

**Connection pooling:** Supabase pooler porta `6543`, modo `transaction`, `pool_size=10` no API.

**Leitura pesada:** preferir `payload JSONB` único — evita 8 JOINs por request.

### 7.5 Views Úteis

```sql
CREATE VIEW v_latest_snapshots AS
SELECT DISTINCT ON (ticker)
    ticker, reference_date, payload, recommendation, composite_score, published_at
FROM stock_analysis_snapshot
ORDER BY ticker, reference_date DESC;
```

---

## 8. Estratégia de APIs Externas

### 8.1 Yahoo Finance (primário MVP)

| Aspecto | Decisão |
|---------|---------|
| Biblioteca | `yfinance` (adapter) com wrapper rate-limit |
| Símbolo B3 | `ITUB4.SA` (conversão automática `ticker_to_yahoo()`) |
| Dados coletados | OHLCV 2y, info dict, dividends, financials quarterly |
| Frequência | Diária (preço); fundamentals 1x/semana ou após earnings |
| Cache | `provider_cache` 24h por `(ticker, data_type)` |
| Fallback | `brapi.dev` para tickers com falha Yahoo |

```python
class YahooFinanceAdapter(MarketDataPort):
    async def get_quotes(self, tickers: list[str]) -> list[QuoteDTO]: ...
    async def get_fundamentals(self, ticker: str) -> FundamentalsDTO: ...
```

**Limitações conhecidas:**
- Não oficial; pode quebrar sem aviso → monitorar taxa de erro
- Rate limit agressivo → semaphore + cache obrigatório
- Dados B3 podem ter atraso → exibir `data_freshness` na UI

### 8.2 Notícias

| Provider | Uso | Custo |
|----------|-----|-------|
| Yahoo Finance news | Primário | Incluído |
| RSS (InfoMoney, B3 comunicados) | Secundário | Grátis |
| NewsAPI.org | Fase 2 | Pago |

**Pipeline:** fetch → dedupe `url_hash` → match ticker → `stock_news` → sentiment rules.

### 8.3 Sentiment Analysis (MVP — sem LLM)

```python
# backend/core/sentiment/rule_sentiment_analyzer.py

NEGATIVE_KEYWORDS = ["fraude", "investigação", "downgrade", "prejuízo", ...]
POSITIVE_KEYWORDS = ["recorde", "dividendo", "upgrade", "lucro", ...]

def analyze(text: str) -> Sentiment:
    score = count_pos(text) - count_neg(text)
    if score >= 2: return Sentiment.POSITIVE
    if score <= -2: return Sentiment.NEGATIVE
    return Sentiment.NEUTRAL
```

**Agregação por ticker:** % negativas na semana → flag de risco `NEGATIVE_NEWS_CLUSTER` (regra em `RiskRuleEngine`).

**Fase 2:** FinBERT local ou OpenAI batch com custo controlado — nunca em request síncrono.

### 8.4 Matriz de Resiliência

| Provider | Timeout | Retry | Circuit breaker |
|----------|---------|-------|-----------------|
| Yahoo | 15s | 5x exp backoff | 10 falhas → skip 1h |
| RSS | 10s | 3x | por feed |
| OpenAI | 60s | 3x | reduzir batch size |

---

## 9. Estratégia de Frontend

### 9.1 Server vs Client Components

| Componente | Tipo | Motivo |
|------------|------|--------|
| `page.tsx` (stock, ranking) | **Server** | SEO, LCP, dados no HTML |
| `layout.tsx` | **Server** | metadata |
| `search-bar.tsx` | **Client** | debounce, keyboard |
| `score-breakdown-chart.tsx` | **Client** | recharts interativo |
| `recommendation-badge.tsx` | **Server** | estático |
| `ai-explanation.tsx` | **Server** | texto pré-renderizado |
| `use-recent-tickers.ts` | **Client** | localStorage |

### 9.2 Busca de Dados (Server)

```typescript
// frontend/lib/api/stocks.ts
import { cache } from 'react';

export const getStockSnapshot = cache(async (ticker: string): Promise<StockSnapshot> => {
  const res = await fetch(`${API_URL}/api/v1/stocks/${ticker}`, {
    next: { tags: [`snapshot:${ticker}`], revalidate: 3600 },
  });
  if (!res.ok) throw notFound();
  return res.json();
});
```

### 9.3 Cache em Camadas

| Camada | Mecanismo | TTL |
|--------|-----------|-----|
| CDN Vercel | ISR / `Cache-Control` | ranking 24h |
| Next.js Data Cache | `revalidate`, `tags` | snapshot 1h |
| Redis (API) | `snapshot:{ticker}:{date}` | 1h |
| Browser | `localStorage` recent tickers | ∞ |

**Invalidação pós-batch:**

```typescript
// frontend/app/api/revalidate/route.ts
export async function POST(req: Request) {
  const secret = req.headers.get('x-revalidate-secret');
  if (secret !== process.env.REVALIDATE_SECRET) return new Response('Unauthorized', { status: 401 });
  const { tickers } = await req.json();
  revalidateTag('ranking:dividends');
  tickers?.forEach((t: string) => revalidateTag(`snapshot:${t}`));
  return Response.json({ revalidated: true });
}
```

### 9.4 SEO

```typescript
// app/stock/[ticker]/page.tsx
export async function generateMetadata({ params }): Promise<Metadata> {
  const snap = await getStockSnapshot(params.ticker);
  return {
    title: `${snap.ticker} — ${snap.company_name} | Análise e Recomendação`,
    description: `Score ${snap.scores.composite}. Recomendação: ${snap.recommendation}. Dividendos, fundamentos e riscos.`,
    openGraph: { ... },
    robots: { index: true },
  };
}
```

- `sitemap.xml` dinâmico com tickers ativos
- JSON-LD `FinancialProduct` (opcional Fase 2)
- Canonical URLs sem query strings

### 9.5 Loading e Error States

| Rota | `loading.tsx` | `error.tsx` |
|------|---------------|-------------|
| `/stock/[ticker]` | Skeleton das 8 seções | Boundary + retry |
| `/ranking/dividends` | Table skeleton | Fallback ranking D-1 |
| `/` | Search skeleton | — |

**Stale banner:** se `reference_date < today` → `<StaleDataBanner date={...} />`.

### 9.6 Design System

- **shadcn/ui** + Tailwind tokens semânticos
- Cores de recomendação: BUY verde, HOLD âmbar, SELL vermelho (acessível WCAG AA)
- Mobile-first; tabelas → cards em `<md`

---

## 10. Estratégia de Autenticação Futura

### 10.1 MVP

- Leitura **pública** sem login
- Rate limit por IP (API + middleware)
- Feedback anônimo com `ip_hash` (sha256 + salt)

### 10.2 Fase 2 — Supabase Auth

```text
┌──────────────┐     JWT      ┌──────────────┐
│  Next.js     │ ◄──────────► │ Supabase Auth│
│  @supabase/  │              │ (email/OAuth)│
│  ssr         │              └──────────────┘
└──────┬───────┘
       │ RLS policies
       ▼
┌──────────────┐
│  PostgreSQL  │
│  watchlists  │
│  user_prefs  │
└──────────────┘
```

**Tabelas futuras:**

```sql
CREATE TABLE watchlists (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id),
    name VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE watchlist_items (
    watchlist_id UUID REFERENCES watchlists(id),
    stock_id UUID REFERENCES stocks(id),
    PRIMARY KEY (watchlist_id, stock_id)
);
```

**RLS:**

```sql
ALTER TABLE watchlists ENABLE ROW LEVEL SECURITY;
CREATE POLICY "user owns watchlist" ON watchlists
  FOR ALL USING (auth.uid() = user_id);
```

**API:** endpoints `/api/v1/watchlist` exigem `Authorization: Bearer <jwt>`; FastAPI valida JWT via Supabase JWKS.

---

## 11. Estratégia de Observabilidade

### 11.1 Logs (Structured JSON)

```python
logger.info(
    "batch_step_completed",
    extra={
        "step": "compute_scores",
        "reference_date": str(ref_date),
        "tickers_ok": 198,
        "tickers_failed": 2,
        "duration_ms": 45000,
        "run_id": str(run_id),
    },
)
```

| Campo obrigatório | Onde |
|-------------------|------|
| `request_id` | HTTP + batch |
| `ticker` | logs por ação |
| `reference_date` | batch |
| `duration_ms` | performance |

**Destino MVP:** stdout → Vercel Logs / Fly logs; GitHub Actions artifacts.

### 11.2 Tracing

| Ferramenta | Escopo MVP | Escopo Growth |
|------------|------------|---------------|
| **Sentry** | Errors FE + BE + batch | Performance monitoring |
| **OpenTelemetry** | Opcional | Full traces API → PG |

```python
# FastAPI middleware
from sentry_sdk.integrations.fastapi import FastApiIntegration
sentry_sdk.init(dsn=..., integrations=[FastApiIntegration()])
```

### 11.3 Monitoramento e Alertas

| Alerta | Condição | Canal |
|--------|----------|-------|
| Batch falhou | `batch_job_runs.status = FAILED` | Email / Slack webhook |
| API 5xx rate | > 1% em 5min | Sentry |
| Latência p95 | > 500ms 15min | Vercel Analytics |
| OpenAI cost | tokens/dia > threshold | Log diário |
| Yahoo error rate | > 10% tickers | Batch report |

### 11.4 Health Checks

```http
GET /api/v1/health
→ { "status": "ok", "db": "ok", "redis": "ok", "latest_snapshot_date": "2026-05-19" }
```

### 11.5 Métricas de Produto (não infra)

- PostHog ou Plausible no frontend (sem PII)
- Eventos: `search`, `view_stock`, `feedback_helpful`

---

## 12. Estratégia de Deploy

### 12.1 Ambientes

| Ambiente | Frontend | API | DB | Batch |
|----------|----------|-----|-----|-------|
| **local** | `pnpm dev` | `uvicorn` | Docker PG | manual / APScheduler |
| **preview** | Vercel PR | Fly preview | Supabase branch | GHA manual |
| **staging** | Vercel | Fly | Supabase staging | cron staging |
| **production** | Vercel | Fly | Supabase prod | cron 02:00 BRT |

### 12.2 CI/CD (GitHub Actions)

```yaml
# .github/workflows/ci.yml — em todo PR
- lint (ruff, eslint)
- test (pytest, vitest)
- build docker images

# .github/workflows/deploy-api.yml — main
- deploy Fly.io backend/api

# .github/workflows/nightly-batch.yml — schedule
- docker run backend/batch --reference-date ${{ }}
- on success: curl revalidate webhook
```

### 12.3 Variáveis de Ambiente

| Variável | Onde | Secreto |
|----------|------|---------|
| `DATABASE_URL` | API, Batch | Sim |
| `REDIS_URL` | API, Batch | Sim |
| `OPENAI_API_KEY` | Batch only | Sim |
| `NEXT_PUBLIC_API_URL` | Vercel | Não |
| `REVALIDATE_SECRET` | Vercel, Batch | Sim |
| `SENTRY_DSN` | Todos | Sim |
| `SUPABASE_SERVICE_ROLE_KEY` | Next server only | Sim |

### 12.4 Vercel — Next.js

```json
// vercel.json (opcional)
{
  "rewrites": [
    { "source": "/api/v1/:path*", "destination": "https://api.seudominio.com/api/v1/:path*" }
  ]
}
```

---

## 13. Estratégia de Ambiente Local

### 13.1 Pré-requisitos

- Node 20+, pnpm 9+
- Python 3.12+, uv ou poetry
- Docker Desktop
- Conta OpenAI (dev batch manual)

### 13.2 Setup Rápido

```bash
# 1. Infra local
docker compose up -d postgres redis

# 2. Python
uv sync
alembic upgrade head
python -m batch --job seed_dev --tickers ITUB4,BBAS3

# 3. Frontend
pnpm install
cp frontend/.env.local.example frontend/.env.local
pnpm --filter frontend dev

# 4. API
uvicorn app.main:app --reload --port 8000
```

### 13.3 `.env.example` (raiz)

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/stock_analysis

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI (batch dev only)
OPENAI_API_KEY=sk-...

# API
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000

# Next.js
NEXT_PUBLIC_API_URL=http://localhost:8000
REVALIDATE_SECRET=dev-secret

# Feature flags
ENABLE_LIVE_LLM=false
MOCK_MARKET_DATA=false
```

### 13.4 APScheduler Local

```python
# backend/batch/src/batch/scheduler.py
scheduler.add_job(run_pipeline, "cron", hour=2, minute=0, timezone="America/Sao_Paulo")
```

Usar apenas em dev; produção usa GHA.

---

## 14. Estratégia Docker

### 14.1 `docker-compose.yml` (desenvolvimento)

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: stock_analysis
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  # Opcional: API local containerizada
  api:
    build: { context: ., dockerfile: backend/api/Dockerfile }
    env_file: .env
    ports: ["8000:8000"]
    depends_on: [postgres, redis]

volumes:
  pgdata:
```

### 14.2 Dockerfile — API (multi-stage)

```dockerfile
# backend/api/Dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY backend/api ./backend/api
COPY backend/core ./backend/core
ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 14.3 Dockerfile — Batch

```dockerfile
# backend/batch/Dockerfile
FROM python:3.12-slim
WORKDIR /app
# ... similar
ENTRYPOINT ["python", "-m", "batch"]
```

### 14.4 Produção

- **Não** rodar batch em container 24/7 no MVP
- GHA executa `docker run --rm batch:latest run_pipeline`
- Imagens no GHCR (`ghcr.io/org/stock-batch:sha`)

---

## 15. Roadmap Técnico do MVP

### Semana 1–2 — Fundação

| Entrega | Critério de pronto |
|---------|-------------------|
| Monorepo pnpm + uv workspace | CI verde |
| Docker compose PG + Redis | `alembic upgrade head` OK |
| Schema core + seeds 10 tickers | migrations versionadas |
| `RecommendationEngine` + testes golden | 100% fixtures |
| FastAPI skeleton + `/health` | deploy Fly staging |

### Semana 3–5 — Pipeline de Dados

| Entrega | Critério de pronto |
|---------|-------------------|
| `YahooFinanceAdapter` + cache | 50 tickers ingest |
| Pipeline completo CLI | snapshot publicado |
| GHA nightly-batch.yml | run automático staging |
| `RuleSentimentAnalyzer` | flags em risk |

### Semana 6–9 — API + Frontend

| Entrega | Critério de pronto |
|---------|-------------------|
| Endpoints search, stock, ranking | p95 < 300ms |
| Next.js páginas SSR/ISR | LCP < 2.5s |
| Redis cache API | hit rate > 80% após warmup |
| Sentry integrado | errors rastreáveis |

### Semana 10–12 — IA + Produção

| Entrega | Critério de pronto |
|---------|-------------------|
| Narrativas batch + validador | 0 contradições em test set |
| 200 tickers produção | batch < 4h |
| Revalidate webhook | cache invalida pós-batch |
| Load test 100 RPS leitura | sem degradação |
| Documentação runbook | on-call playbook |

---

## 16. Riscos Técnicos e Mitigação

| Risco | Prob. | Impacto | Mitigação |
|-------|-------|---------|-----------|
| Yahoo Finance instável | Alta | Alto | Brapi fallback; provider_cache; monitorar error rate |
| Limite Vercel serverless Python | Média | Médio | FastAPI no Fly; Next só TS |
| Alucinação LLM | Média | Alto | Validador + template fallback; temperature 0.2 |
| Batch estoura 6h GHA | Baixa | Alto | Chunks paralelos; incremental; timeout por step |
| Custo OpenAI escala | Média | Médio | Gate delta score; finops dashboard |
| Supabase connection limit | Média | Médio | Pooler; pgBouncer; read replicas |
| JSON snapshot grande | Baixa | Médio | Comprimir campos; paginar notícias |
| Regulatório (recomendação) | Média | Alto | Disclaimers; logs de scoring_version |

---

## 17. Design Patterns Recomendados

| Pattern | Onde aplicar | Benefício |
|---------|--------------|-----------|
| **Hexagonal (Ports & Adapters)** | `ingestion/adapters` | Troca Yahoo → outro provider |
| **Repository** | API + batch repos | Testabilidade, SQL isolado |
| **Unit of Work** | Batch writes | Transações consistentes |
| **CQRS light** | metrics/scores write vs snapshot read | Performance leitura |
| **Strategy** | Scorers (fundamental, dividend, technical) | Extensão de métricas |
| **Factory** | `ScorerFactory` por versão config | scoring A/B |
| **Builder** | `SnapshotBuilder` | JSON snapshot complexo |
| **Chain of Responsibility** | `RiskRuleEngine` | Novas regras de risco |
| **Template Method** | `BaseBatchJob.run()` | retry/logging padronizado |
| **Result/Either** | domain errors | sem exceptions para fluxo esperado |
| **Dependency Injection** | FastAPI `Depends()` | testes com overrides |
| **Cache-Aside** | Redis + API | latência |

**Anti-patterns a evitar:**

- LLM no controller
- JOINs na hot path de leitura
- Lógica de score no frontend
- Batch não idempotente
- Secrets no `NEXT_PUBLIC_*`

---

## 18. Estratégia de Crescimento Futuro

### 18.1 Escalabilidade Horizontal

| Componente | Escala |
|------------|--------|
| Next.js | Vercel auto |
| FastAPI | Fly replicas + load balancer |
| PostgreSQL | Supabase Pro + read replica |
| Batch | Split por setor; filas SQS + workers (Fase 3) |
| Redis | Upstash cluster |

### 18.2 Evolução Arquitetural por Fase

```text
MVP (agora)          Growth (1k-10k DAU)       Scale (10k+ DAU)
─────────────        ───────────────────       ─────────────────
Modular monolith     + Read replica            + Event queue (SQS/Rabbit)
GHA batch            + Dedicated worker        + Kubernetes jobs
Single region        + CDN BR edge             + Multi-region read
Rule sentiment       + FinBERT batch           + Feature store
Supabase Auth        + Stripe premium          + API pública
```

### 18.3 API Pública (Fase 3)

- Rate limit por API key
- Plano free: 100 req/dia
- OpenAPI 3.1 gerado pelo FastAPI
- Versionamento `/api/v2`

### 18.4 Feature Flags

```python
# config.py
ENABLE_US_TICKERS: bool = False
ENABLE_LIVE_LLM: bool = False  # nunca true no MVP
ENABLE_SENTIMENT_LLM: bool = False
```

Usar variáveis de ambiente + tabela `feature_flags` para rollout gradual.

### 18.5 FinOps Contínuo

- Dashboard mensal: Vercel + Supabase + OpenAI + Fly
- Alerta se custo > US$ 150/mês
- Revisão trimestral de scoring weights sem deploy (tabela `scoring_config`)

---

## Apêndice A — Contratos API (Resumo)

| Método | Path | Auth | Cache |
|--------|------|------|-------|
| GET | `/api/v1/stocks/search?q=` | Não | 5min |
| GET | `/api/v1/stocks/{ticker}` | Não | 1h |
| GET | `/api/v1/rankings/dividends?date=` | Não | 24h |
| GET | `/api/v1/health` | Não | — |
| POST | `/api/v1/feedback` | Não | — |

## Apêndice B — Checklist Production-Ready

- [ ] Migrations Alembic em CI
- [ ] Secrets rotacionados
- [ ] Rate limit ativo
- [ ] RLS preparado (desligado MVP, scripts prontos)
- [ ] Backup Supabase habilitado
- [ ] Batch idempotente testado (re-run 2x mesmo resultado)
- [ ] Golden tests scoring
- [ ] Validador IA com test fixtures
- [ ] Runbook batch failure
- [ ] Disclaimers na UI
- [ ] `ENABLE_LIVE_LLM=false` em produção

## Apêndice C — Referência Cruzada PRD

| PRD | Arquitetura |
|-----|-------------|
| RN-01..04 | §4, §6 |
| RF-API-* | §4, Apêndice A |
| RF-BATCH-* | §5 |
| RNF-P01 | §9, §7 |
| scoring_config | §7.2 |
| dividend_rank_score | §2, §7 |

---

*Fim da Arquitetura Técnica v1.0*

# Stock Analysis — Frontend

Next.js 15 app (App Router) para a plataforma de análise de ações.

## Requisitos

- Node.js **20.9+** (recomendado; Next 15 e Tailwind 4 exigem Node 20+)
- npm 10+

## Setup

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Abra [http://localhost:3000](http://localhost:3000).

## Scripts

| Comando | Descrição |
|---------|-----------|
| `npm run dev` | Servidor de desenvolvimento |
| `npm run build` | Build de produção |
| `npm run start` | Servidor de produção |
| `npm run lint` | ESLint |
| `npm run format` | Prettier |

## Estrutura

```
frontend/
├── app/              # App Router (rotas)
├── components/       # UI compartilhada (layout, shadcn)
├── features/         # Módulos por domínio (home, search, ranking, stock)
├── hooks/
├── lib/
├── services/api/     # Cliente HTTP + mocks
├── types/
└── config/
```

## Mock API

Com `NEXT_PUBLIC_USE_MOCK_API=true`, a UI funciona sem backend (dados de ITUB4, BBAS3, etc.).

## Deploy

Otimizado para **Vercel**. Configure `NEXT_PUBLIC_API_URL` apontando para o FastAPI em produção.

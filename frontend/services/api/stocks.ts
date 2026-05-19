import { cache } from "react";

import { cacheTags } from "@/lib/cache/tags";
import { apiClient } from "@/services/api/client";
import type { StockSearchHit, StockSnapshot } from "@/types/stock";

import { getMockSnapshot, mockSearch } from "./mocks";

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK_API === "true";

type ApiStockSearchHit = {
  ticker: string;
  company_name: string;
  sector?: string | null;
};

type ApiStockSnapshot = {
  ticker: string;
  company_name: string;
  sector?: string | null;
  reference_date: string;
  recommendation: StockSnapshot["recommendation"];
  composite_score: string | number;
  dividend_yield?: string | number | null;
  score_breakdown?: {
    fundamental?: string | number | null;
    dividend?: string | number | null;
    technical?: string | number | null;
    risk?: string | number | null;
  };
  ai_summary?: string | null;
  risk_flags?: string[];
  updated_at: string;
};

function toNumber(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function mapSearchHit(hit: ApiStockSearchHit): StockSearchHit {
  return {
    ticker: hit.ticker,
    name: hit.company_name,
    sector: hit.sector ?? undefined,
  };
}

function mapSnapshot(snapshot: ApiStockSnapshot): StockSnapshot {
  const scoreBreakdown = snapshot.score_breakdown ?? {};
  const composite = toNumber(snapshot.composite_score) ?? 0;
  const dividendYield = toNumber(snapshot.dividend_yield);

  return {
    ticker: snapshot.ticker,
    companyName: snapshot.company_name,
    referenceDate: snapshot.reference_date,
    recommendation: snapshot.recommendation,
    scores: {
      fundamental: {
        score: toNumber(scoreBreakdown.fundamental),
        highlights: [],
      },
      dividend: {
        score: toNumber(scoreBreakdown.dividend),
        highlights: dividendYield === null ? [] : [`Yield ${(dividendYield * 100).toFixed(2)}%`],
      },
      technical: {
        score: toNumber(scoreBreakdown.technical),
        highlights: [],
      },
      composite,
    },
    companySummary:
      snapshot.ai_summary ??
      `${snapshot.company_name} e uma empresa listada na B3${snapshot.sector ? ` no setor ${snapshot.sector}` : ""}.`,
    aiExplanation:
      snapshot.ai_summary ??
      `Recomendacao ${snapshot.recommendation} baseada no score composto ${composite.toFixed(2)}.`,
    dataFreshness: {
      pricesUpdatedAt: snapshot.updated_at,
      fundamentalsLabel: snapshot.reference_date,
    },
    scoringVersion: "1.0.0",
  };
}

export const searchStocks = cache(async (query: string): Promise<StockSearchHit[]> => {
  if (!query.trim()) return [];
  if (USE_MOCK) return mockSearch(query);

  const hits = await apiClient<ApiStockSearchHit[]>(
    `/api/v1/stocks/search?q=${encodeURIComponent(query)}`,
    { next: { revalidate: 300 } },
  );
  return hits.map(mapSearchHit);
});

export const getStockSnapshot = cache(async (ticker: string): Promise<StockSnapshot | null> => {
  const normalized = ticker.toUpperCase();
  if (USE_MOCK) return getMockSnapshot(normalized);

  try {
    const snapshot = await apiClient<ApiStockSnapshot>(`/api/v1/stocks/${normalized}`, {
      next: {
        tags: [cacheTags.snapshot(normalized)],
        revalidate: 3600,
      },
    });
    return mapSnapshot(snapshot);
  } catch {
    return null;
  }
});

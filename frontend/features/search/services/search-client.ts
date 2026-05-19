"use client";

import { mockSearch } from "@/services/api/mocks";
import type { StockSearchHit } from "@/types/stock";

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK_API === "true";

type ApiStockSearchHit = {
  ticker: string;
  company_name: string;
  sector?: string | null;
};

function mapSearchHit(hit: ApiStockSearchHit): StockSearchHit {
  return {
    ticker: hit.ticker,
    name: hit.company_name,
    sector: hit.sector ?? undefined,
  };
}

export async function searchStocksClient(query: string): Promise<StockSearchHit[]> {
  if (USE_MOCK) return mockSearch(query);

  const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const res = await fetch(`${base}/api/v1/stocks/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) return [];
  const hits = (await res.json()) as ApiStockSearchHit[];
  return hits.map(mapSearchHit);
}

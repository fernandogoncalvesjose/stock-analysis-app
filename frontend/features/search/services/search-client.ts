"use client";

import { mockSearch } from "@/services/api/mocks";
import type { StockSearchHit } from "@/types/stock";

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK_API !== "false";

export async function searchStocksClient(query: string): Promise<StockSearchHit[]> {
  if (USE_MOCK) return mockSearch(query);

  const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const res = await fetch(`${base}/api/v1/stocks/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) return [];
  return res.json();
}

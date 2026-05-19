import { cache } from "react";

import { cacheTags } from "@/lib/cache/tags";
import { apiClient } from "@/services/api/client";
import type { StockSearchHit, StockSnapshot } from "@/types/stock";

import { getMockSnapshot, mockSearch } from "./mocks";

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK_API !== "false";

export const searchStocks = cache(async (query: string): Promise<StockSearchHit[]> => {
  if (!query.trim()) return [];
  if (USE_MOCK) return mockSearch(query);

  return apiClient<StockSearchHit[]>(
    `/api/v1/stocks/search?q=${encodeURIComponent(query)}`,
    { next: { revalidate: 300 } },
  );
});

export const getStockSnapshot = cache(async (ticker: string): Promise<StockSnapshot | null> => {
  const normalized = ticker.toUpperCase();
  if (USE_MOCK) return getMockSnapshot(normalized);

  try {
    return await apiClient<StockSnapshot>(`/api/v1/stocks/${normalized}`, {
      next: {
        tags: [cacheTags.snapshot(normalized)],
        revalidate: 3600,
      },
    });
  } catch {
    return null;
  }
});

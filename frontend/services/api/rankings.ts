import { cache } from "react";

import { cacheTags } from "@/lib/cache/tags";
import { apiClient } from "@/services/api/client";
import type { DividendRanking } from "@/types/ranking";

import { getMockRanking } from "./mocks";

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK_API === "true";

type ApiDividendRankingItem = {
  position: number;
  ticker: string;
  company_name: string;
  sector?: string | null;
  dividend_yield?: string | number | null;
  composite_score: string | number;
  recommendation: DividendRanking["items"][number]["recommendation"];
};

type ApiDividendRanking = {
  reference_date: string | null;
  items: ApiDividendRankingItem[];
};

function toNumber(value: string | number | null | undefined): number {
  if (value === null || value === undefined) return 0;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function mapRanking(ranking: ApiDividendRanking): DividendRanking {
  return {
    referenceDate: ranking.reference_date ?? new Date().toISOString().slice(0, 10),
    items: ranking.items.map((item) => {
      const compositeScore = toNumber(item.composite_score);
      return {
        rank: item.position,
        ticker: item.ticker,
        name: item.company_name,
        dividendYield: toNumber(item.dividend_yield) * 100,
        safetyScore: compositeScore,
        recommendation: item.recommendation,
        rankChange: null,
        compositeScore,
      };
    }),
  };
}

export const getDividendRanking = cache(
  async (date?: string): Promise<DividendRanking> => {
    if (USE_MOCK) return getMockRanking();

    const query = date ? `?date=${date}` : "";
    const ranking = await apiClient<ApiDividendRanking>(`/api/v1/rankings/dividends${query}`, {
      next: {
        tags: [cacheTags.ranking],
        revalidate: 86400,
      },
    });
    return mapRanking(ranking);
  },
);

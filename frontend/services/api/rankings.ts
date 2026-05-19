import { cache } from "react";

import { cacheTags } from "@/lib/cache/tags";
import { apiClient } from "@/services/api/client";
import type { DividendRanking } from "@/types/ranking";

import { getMockRanking } from "./mocks";

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK_API !== "false";

export const getDividendRanking = cache(
  async (date?: string): Promise<DividendRanking> => {
    if (USE_MOCK) return getMockRanking();

    const query = date ? `?date=${date}` : "";
    return apiClient<DividendRanking>(`/api/v1/rankings/dividends${query}`, {
      next: {
        tags: [cacheTags.ranking],
        revalidate: 86400,
      },
    });
  },
);

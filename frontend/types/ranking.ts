import type { Recommendation } from "@/types/recommendation";

export type DividendRankingItem = {
  rank: number;
  ticker: string;
  name: string;
  dividendYield: number;
  safetyScore: number;
  recommendation: Recommendation;
  rankChange: number | null;
  compositeScore: number;
};

export type DividendRanking = {
  referenceDate: string;
  items: DividendRankingItem[];
};

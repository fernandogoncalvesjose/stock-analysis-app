import type { Recommendation } from "@/types/recommendation";

export type StockSearchHit = {
  ticker: string;
  name: string;
  sector?: string;
};

export type SubScore = {
  score: number | null;
  highlights: string[];
};

export type StockSnapshot = {
  ticker: string;
  companyName: string;
  referenceDate: string;
  recommendation: Recommendation;
  scores: {
    fundamental: SubScore;
    dividend: SubScore;
    technical: SubScore;
    composite: number;
  };
  companySummary: string;
  aiExplanation: string;
  dataFreshness: {
    pricesUpdatedAt: string;
    fundamentalsLabel: string;
  };
  scoringVersion: string;
};

import type { DividendRanking } from "@/types/ranking";
import type { StockSearchHit, StockSnapshot } from "@/types/stock";

const MOCK_TICKERS: StockSearchHit[] = [
  { ticker: "ITUB4", name: "Itaú Unibanco", sector: "Financeiro" },
  { ticker: "BBAS3", name: "Banco do Brasil", sector: "Financeiro" },
  { ticker: "VALE3", name: "Vale", sector: "Materiais Básicos" },
  { ticker: "PETR4", name: "Petrobras", sector: "Petróleo e Gás" },
  { ticker: "WEGE3", name: "WEG", sector: "Bens Industriais" },
];

export function mockSearch(query: string): StockSearchHit[] {
  const q = query.toUpperCase();
  return MOCK_TICKERS.filter(
    (t) => t.ticker.includes(q) || t.name.toUpperCase().includes(q),
  ).slice(0, 8);
}

export function getMockSnapshot(ticker: string): StockSnapshot | null {
  const hit = MOCK_TICKERS.find((t) => t.ticker === ticker);
  if (!hit) return null;

  return {
    ticker: hit.ticker,
    companyName: hit.name,
    referenceDate: new Date().toISOString().slice(0, 10),
    recommendation: "BUY",
    scores: {
      fundamental: { score: 78, highlights: ["ROE acima do setor", "Margens estáveis"] },
      dividend: { score: 82, highlights: ["Yield 8,2%", "Payout consistente"] },
      technical: { score: 65, highlights: ["SMA50 > SMA200"] },
      composite: 76.4,
    },
    companySummary: `${hit.name} é uma empresa listada na B3 no setor ${hit.sector ?? "N/A"}.`,
    aiExplanation:
      "A recomendação de compra reflete score fundamental sólido, perfil atrativo de dividendos e técnica neutra a positiva.",
    dataFreshness: {
      pricesUpdatedAt: new Date().toISOString().slice(0, 10),
      fundamentalsLabel: "Q1 2026",
    },
    scoringVersion: "1.0.0",
  };
}

export function getMockRanking(): DividendRanking {
  return {
    referenceDate: new Date().toISOString().slice(0, 10),
    items: MOCK_TICKERS.map((t, i) => ({
      rank: i + 1,
      ticker: t.ticker,
      name: t.name,
      dividendYield: 8.5 - i * 0.4,
      safetyScore: 85 - i * 3,
      recommendation: i < 3 ? "BUY" : "HOLD",
      rankChange: i === 0 ? 1 : i === 2 ? -1 : 0,
      compositeScore: 80 - i * 2,
    })),
  };
}

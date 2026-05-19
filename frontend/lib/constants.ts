export const B3_TICKER_REGEX = /^[A-Z]{4}\d{1,2}$/;

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const DISCLAIMER =
  "Recomendação baseada em modelo quantitativo. Não constitui recomendação de investimento.";

export const RECOMMENDATION_LABELS = {
  BUY: "Comprar",
  HOLD: "Manter",
  SELL: "Vender",
} as const;

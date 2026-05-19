export const cacheTags = {
  ranking: "ranking:dividends",
  snapshot: (ticker: string) => `snapshot:${ticker.toUpperCase()}`,
} as const;

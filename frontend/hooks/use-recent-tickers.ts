"use client";

import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "recent-tickers";
const MAX_ITEMS = 8;

export function useRecentTickers() {
  const [recent, setRecent] = useState<string[]>([]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) setRecent(JSON.parse(raw) as string[]);
    } catch {
      setRecent([]);
    }
  }, []);

  const addRecent = useCallback((ticker: string) => {
    setRecent((prev) => {
      const next = [ticker.toUpperCase(), ...prev.filter((t) => t !== ticker.toUpperCase())].slice(
        0,
        MAX_ITEMS,
      );
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  return { recent, addRecent };
}

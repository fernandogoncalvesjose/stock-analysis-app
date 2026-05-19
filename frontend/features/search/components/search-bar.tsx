"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, useTransition } from "react";
import { Search } from "lucide-react";

import { Input } from "@/components/ui/input";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { useRecentTickers } from "@/hooks/use-recent-tickers";
import { cn } from "@/lib/utils";
import { searchStocksClient } from "@/features/search/services/search-client";
import type { StockSearchHit } from "@/types/stock";

type SearchBarProps = {
  className?: string;
  autoFocus?: boolean;
};

export function SearchBar({ className, autoFocus }: SearchBarProps) {
  const router = useRouter();
  const { addRecent } = useRecentTickers();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<StockSearchHit[]>([]);
  const [open, setOpen] = useState(false);
  const [isPending, startTransition] = useTransition();
  const debouncedQuery = useDebouncedValue(query, 280);

  useEffect(() => {
    if (debouncedQuery.length < 2) {
      setResults([]);
      return;
    }

    startTransition(async () => {
      const hits = await searchStocksClient(debouncedQuery);
      setResults(hits);
    });
  }, [debouncedQuery]);

  const goToTicker = (ticker: string) => {
    addRecent(ticker);
    setOpen(false);
    setQuery("");
    router.push(`/stock/${ticker}`);
  };

  return (
    <div className={cn("relative w-full", className)}>
      <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        autoFocus={autoFocus}
        value={query}
        onChange={(e) => {
          setQuery(e.target.value.toUpperCase());
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && query.trim()) goToTicker(query.trim());
        }}
        placeholder="Buscar ticker (ex: ITUB4)"
        className="h-10 pl-9 font-mono"
        aria-label="Buscar ação"
        aria-expanded={open}
      />
      {open && (results.length > 0 || isPending) && (
        <ul
          className="absolute z-50 mt-1 max-h-64 w-full overflow-auto rounded-lg border border-border bg-popover py-1 shadow-lg"
          role="listbox"
        >
          {isPending && results.length === 0 ? (
            <li className="px-3 py-2 text-sm text-muted-foreground">Buscando...</li>
          ) : (
            results.map((hit) => (
              <li key={hit.ticker}>
                <button
                  type="button"
                  className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-accent"
                  onMouseDown={() => goToTicker(hit.ticker)}
                >
                  <span className="font-mono font-semibold">{hit.ticker}</span>
                  <span className="truncate pl-2 text-muted-foreground">{hit.name}</span>
                </button>
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}

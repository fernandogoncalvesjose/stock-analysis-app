import Link from "next/link";

import { RecommendationBadge } from "@/features/stock/components/recommendation-badge";
import { formatPercent, formatScore } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { DividendRankingItem } from "@/types/ranking";

type DividendRankingTableProps = {
  items: DividendRankingItem[];
  compact?: boolean;
};

export function DividendRankingTable({ items, compact }: DividendRankingTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left text-muted-foreground">
            <th className="px-4 py-3 font-medium">#</th>
            <th className="px-4 py-3 font-medium">Ticker</th>
            {!compact && <th className="hidden px-4 py-3 font-medium sm:table-cell">Empresa</th>}
            <th className="px-4 py-3 font-medium">Yield</th>
            <th className="hidden px-4 py-3 font-medium md:table-cell">Segurança</th>
            <th className="px-4 py-3 font-medium">Score</th>
            <th className="px-4 py-3 font-medium">Rec.</th>
            {!compact && <th className="hidden px-4 py-3 font-medium lg:table-cell">Δ</th>}
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr
              key={item.ticker}
              className="border-b border-border/60 transition-colors hover:bg-muted/40"
            >
              <td className="px-4 py-3 font-mono text-muted-foreground">{item.rank}</td>
              <td className="px-4 py-3">
                <Link
                  href={`/stock/${item.ticker}`}
                  className="font-mono font-semibold text-primary hover:underline"
                >
                  {item.ticker}
                </Link>
              </td>
              {!compact && (
                <td className="hidden max-w-[200px] truncate px-4 py-3 sm:table-cell">
                  {item.name}
                </td>
              )}
              <td className="px-4 py-3 font-medium text-buy">
                {formatPercent(item.dividendYield)}
              </td>
              <td className="hidden px-4 py-3 md:table-cell">{formatScore(item.safetyScore)}</td>
              <td className="px-4 py-3">{formatScore(item.compositeScore)}</td>
              <td className="px-4 py-3">
                <RecommendationBadge recommendation={item.recommendation} />
              </td>
              {!compact && (
                <td
                  className={cn(
                    "hidden px-4 py-3 font-mono lg:table-cell",
                    item.rankChange && item.rankChange > 0 && "text-buy",
                    item.rankChange && item.rankChange < 0 && "text-sell",
                  )}
                >
                  {item.rankChange === null
                    ? "—"
                    : item.rankChange > 0
                      ? `+${item.rankChange}`
                      : item.rankChange}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

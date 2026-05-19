import type { Metadata } from "next";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DividendRankingTable } from "@/features/ranking/components/dividend-ranking-table";
import { formatDatePtBr } from "@/lib/format";
import { getDividendRanking } from "@/services/api/rankings";

export const metadata: Metadata = {
  title: "Ranking de Dividendos",
  description: "Top ações da B3 focadas em dividendos, atualizado diariamente.",
};

export const revalidate = 86400;

export default async function DividendRankingPage() {
  const ranking = await getDividendRanking();

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
      <header>
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Ranking de dividendos</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Referência: {formatDatePtBr(ranking.referenceDate)} · Atualizado na madrugada
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Top {ranking.items.length} do dia</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <DividendRankingTable items={ranking.items} />
        </CardContent>
      </Card>
    </div>
  );
}

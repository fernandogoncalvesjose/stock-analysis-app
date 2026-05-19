import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DividendRankingTable } from "@/features/ranking/components/dividend-ranking-table";
import { getDividendRanking } from "@/services/api/rankings";

export async function RankingPreview() {
  const ranking = await getDividendRanking();
  const preview = ranking.items.slice(0, 5);

  return (
    <section id="analises" className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mb-6 flex items-end justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Top dividendos do dia</h2>
          <p className="text-sm text-muted-foreground">
            Atualizado em {ranking.referenceDate} · Pré-processado na madrugada
          </p>
        </div>
        <Button asChild variant="outline" size="sm">
          <Link href="/ranking/dividends">
            Ver ranking completo
            <ArrowRight className="h-4 w-4" />
          </Link>
        </Button>
      </div>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-medium text-muted-foreground">
            Ranking diário
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <DividendRankingTable items={preview} compact />
        </CardContent>
      </Card>
    </section>
  );
}

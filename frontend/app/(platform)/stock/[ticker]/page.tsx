import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RecommendationBadge } from "@/features/stock/components/recommendation-badge";
import { formatDatePtBr, formatScore } from "@/lib/format";
import { getStockSnapshot } from "@/services/api/stocks";

type PageProps = {
  params: Promise<{ ticker: string }>;
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { ticker } = await params;
  const snap = await getStockSnapshot(ticker);
  if (!snap) return { title: "Ação não encontrada" };

  return {
    title: `${snap.ticker} — ${snap.companyName}`,
    description: `Score ${formatScore(snap.scores.composite)} · Recomendação ${snap.recommendation}`,
  };
}

export default async function StockPage({ params }: PageProps) {
  const { ticker } = await params;
  const snapshot = await getStockSnapshot(ticker);

  if (!snapshot) notFound();

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
      <header className="flex flex-col gap-4 border-b border-border pb-6 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="font-mono text-sm text-muted-foreground">{snapshot.ticker}</p>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">{snapshot.companyName}</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Atualizado em {formatDatePtBr(snapshot.dataFreshness.pricesUpdatedAt)} ·{" "}
            {snapshot.dataFreshness.fundamentalsLabel}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-xs text-muted-foreground">Score composto</p>
            <p className="text-3xl font-bold tabular-nums">
              {formatScore(snapshot.scores.composite)}
            </p>
          </div>
          <RecommendationBadge recommendation={snapshot.recommendation} className="text-sm" />
        </div>
      </header>

      <div className="grid gap-4 md:grid-cols-3">
        <ScoreCard title="Fundamentalista" score={snapshot.scores.fundamental.score} />
        <ScoreCard title="Dividendos" score={snapshot.scores.dividend.score} />
        <ScoreCard title="Técnico" score={snapshot.scores.technical.score} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Resumo da empresa</CardTitle>
        </CardHeader>
        <CardContent className="text-muted-foreground">{snapshot.companySummary}</CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Por que esta recomendação?</CardTitle>
        </CardHeader>
        <CardContent className="leading-relaxed text-muted-foreground">
          {snapshot.aiExplanation}
        </CardContent>
      </Card>
    </div>
  );
}

function ScoreCard({ title, score }: { title: string; score: number | null }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-bold tabular-nums">
          {score === null ? "—" : formatScore(score)}
        </p>
      </CardContent>
    </Card>
  );
}

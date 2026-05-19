import type { Metadata } from "next";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { siteConfig } from "@/config/site";

export const metadata: Metadata = {
  title: "Metodologia",
  description: "Como calculamos scores e recomendações.",
};

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
      <h1 className="text-3xl font-bold tracking-tight">Metodologia</h1>
      <p className="mt-2 text-muted-foreground">{siteConfig.description}</p>

      <div className="mt-8 space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Modelo quantitativo</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted-foreground">
            <p>Score composto = 45% fundamental + 35% dividendos + 20% técnico.</p>
            <p>Comprar ≥ 70 · Manter 45–69 · Vender &lt; 45 (limiares configuráveis).</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Papel da IA</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            A IA gera textos explicativos em batch a partir dos scores. Ela não altera
            recomendações nem inventa métricas.
          </CardContent>
        </Card>
      </div>

      <Button asChild className="mt-8">
        <Link href="/">Voltar ao início</Link>
      </Button>
    </div>
  );
}

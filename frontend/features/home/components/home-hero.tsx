import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { SearchBar } from "@/features/search/components/search-bar";

export function HomeHero() {
  return (
    <section className="relative overflow-hidden border-b border-border finance-grid">
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-primary/10 via-transparent to-transparent" />
      <div className="relative mx-auto max-w-7xl px-4 py-12 sm:px-6 sm:py-16 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-border bg-card/80 px-3 py-1 text-xs text-muted-foreground backdrop-blur">
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            Análise quantitativa · Scores pré-processados · IA explicativa
          </p>
          <h1 className="text-balance text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            Decisões de investimento com{" "}
            <span className="text-primary">dados e transparência</span>
          </h1>
          <p className="mt-4 text-pretty text-muted-foreground sm:text-lg">
            Fundamentalista, dividendos e técnica simples para ações da B3. Recomendação
            matemática — a IA apenas explica o resultado.
          </p>
          <div className="mx-auto mt-8 max-w-xl">
            <SearchBar autoFocus />
          </div>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
            <Button asChild size="lg">
              <Link href="/ranking/dividends">
                Ver ranking de dividendos
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link href="/about">Como funciona</Link>
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}

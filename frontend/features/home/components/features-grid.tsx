import { Brain, LineChart, Trophy } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const features = [
  {
    title: "Scores fundamentais",
    description: "P/L, ROE, endividamento e crescimento normalizados por setor.",
    icon: LineChart,
  },
  {
    title: "Foco em dividendos",
    description: "Yield, payout, consistência e ranking diário das melhores pagadoras.",
    icon: Trophy,
  },
  {
    title: "IA explicativa",
    description: "Narrativas geradas em batch a partir dos scores — sem alterar a recomendação.",
    icon: Brain,
  },
];

export function FeaturesGrid() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <h2 className="mb-6 text-2xl font-bold tracking-tight">Por que usar a plataforma</h2>
      <div className="grid gap-4 md:grid-cols-3">
        {features.map((feature) => (
          <Card key={feature.title} className="bg-card/50">
            <CardHeader>
              <feature.icon className="mb-2 h-8 w-8 text-primary" />
              <CardTitle className="text-lg">{feature.title}</CardTitle>
              <CardDescription>{feature.description}</CardDescription>
            </CardHeader>
            <CardContent />
          </Card>
        ))}
      </div>
    </section>
  );
}

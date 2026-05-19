import { BarChart3, Clock, Shield, Zap } from "lucide-react";

const stats = [
  { label: "Atualização diária", value: "02:00 BRT", icon: Clock },
  { label: "Resposta média", value: "< 300ms", icon: Zap },
  { label: "Modelo quantitativo", value: "Auditável", icon: Shield },
  { label: "Cobertura MVP", value: "200+ tickers", icon: BarChart3 },
];

export function StatsStrip() {
  return (
    <section className="border-b border-border bg-surface-elevated/30">
      <div className="mx-auto grid max-w-7xl grid-cols-2 gap-4 px-4 py-6 sm:grid-cols-4 sm:px-6 lg:px-8">
        {stats.map((stat) => (
          <div key={stat.label} className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <stat.icon className="h-4 w-4" />
            </span>
            <div>
              <p className="text-xs text-muted-foreground">{stat.label}</p>
              <p className="text-sm font-semibold">{stat.value}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

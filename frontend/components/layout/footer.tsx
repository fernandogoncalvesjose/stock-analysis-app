import Link from "next/link";

import { siteConfig } from "@/config/site";

export function Footer() {
  return (
    <footer className="border-t border-border bg-surface-elevated/50">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-8 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        <p>
          © {new Date().getFullYear()} {siteConfig.name}. Dados com fins educacionais.
        </p>
        <div className="flex gap-4">
          <Link href="/about" className="hover:text-foreground">
            Metodologia
          </Link>
          <Link href="/ranking/dividends" className="hover:text-foreground">
            Ranking
          </Link>
        </div>
      </div>
    </footer>
  );
}

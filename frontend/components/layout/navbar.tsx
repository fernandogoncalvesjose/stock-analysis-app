import Link from "next/link";
import { LineChart } from "lucide-react";

import { ThemeToggle } from "@/components/layout/theme-toggle";
import { SearchBar } from "@/features/search/components/search-bar";
import { siteConfig } from "@/config/site";

export function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-border/80 bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-7xl items-center gap-4 px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex shrink-0 items-center gap-2 font-semibold">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <LineChart className="h-4 w-4" />
          </span>
          <span className="hidden sm:inline">{siteConfig.name}</span>
        </Link>
        <div className="flex flex-1 justify-center px-2 md:max-w-md md:px-0 lg:max-w-lg">
          <SearchBar className="w-full" />
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}

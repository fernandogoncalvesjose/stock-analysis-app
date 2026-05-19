import type { LucideIcon } from "lucide-react";
import { BarChart3, Home, Info, Trophy } from "lucide-react";

export type NavItem = {
  title: string;
  href: string;
  icon: LucideIcon;
  description?: string;
};

export const mainNav: NavItem[] = [
  {
    title: "Início",
    href: "/",
    icon: Home,
    description: "Busca e visão geral",
  },
  {
    title: "Ranking Dividendos",
    href: "/ranking/dividends",
    icon: Trophy,
    description: "Top ações para dividendos",
  },
  {
    title: "Metodologia",
    href: "/about",
    icon: Info,
    description: "Como calculamos os scores",
  },
];

export const sidebarNav: NavItem[] = [
  ...mainNav.filter((item) => item.href !== "/about"),
  {
    title: "Análises",
    href: "/#analises",
    icon: BarChart3,
    description: "Explore tickers",
  },
];

export const siteConfig = {
  name: "Stock Analysis",
  description:
    "Análise fundamentalista, dividendos e recomendações quantitativas para ações da B3.",
  url: process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000",
  links: {
    github: "https://github.com",
    docs: "/about",
  },
} as const;

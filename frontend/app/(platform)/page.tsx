import { Suspense } from "react";

import { FeaturesGrid } from "@/features/home/components/features-grid";
import { HomeHero } from "@/features/home/components/home-hero";
import { RankingPreview } from "@/features/home/components/ranking-preview";
import { RankingPreviewSkeleton } from "@/features/home/components/ranking-preview-skeleton";
import { StatsStrip } from "@/features/home/components/stats-strip";

export default function HomePage() {
  return (
    <>
      <HomeHero />
      <StatsStrip />
      <Suspense fallback={<RankingPreviewSkeleton />}>
        <RankingPreview />
      </Suspense>
      <FeaturesGrid />
    </>
  );
}

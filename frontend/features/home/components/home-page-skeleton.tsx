import { Skeleton } from "@/components/ui/skeleton";
import { RankingPreviewSkeleton } from "@/features/home/components/ranking-preview-skeleton";

export function HomePageSkeleton() {
  return (
    <>
      <div className="border-b border-border px-4 py-16 sm:px-6">
        <div className="mx-auto flex max-w-3xl flex-col items-center gap-4">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-10 w-full max-w-xl" />
        </div>
      </div>
      <RankingPreviewSkeleton />
    </>
  );
}

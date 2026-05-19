import { Badge } from "@/components/ui/badge";
import { RECOMMENDATION_LABELS } from "@/lib/constants";
import type { Recommendation } from "@/types/recommendation";

const variantMap = {
  BUY: "buy",
  HOLD: "hold",
  SELL: "sell",
} as const;

export function RecommendationBadge({
  recommendation,
  className,
}: {
  recommendation: Recommendation;
  className?: string;
}) {
  return (
    <Badge variant={variantMap[recommendation]} className={className}>
      {RECOMMENDATION_LABELS[recommendation]}
    </Badge>
  );
}

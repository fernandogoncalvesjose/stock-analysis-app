import { AlertTriangle } from "lucide-react";

import { DISCLAIMER } from "@/lib/constants";

export function DisclaimerBanner() {
  return (
    <div className="border-b border-border/60 bg-muted/40">
      <div className="mx-auto flex max-w-7xl items-center gap-2 px-4 py-2 text-xs text-muted-foreground sm:px-6 lg:px-8">
        <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-hold" aria-hidden />
        <p>{DISCLAIMER}</p>
      </div>
    </div>
  );
}

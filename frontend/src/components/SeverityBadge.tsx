import { cn } from "@/lib/utils";
import { SEVERITY_META } from "@/lib/constants";
import type { Severity } from "@/types/api";

export function SeverityBadge({ severity, className }: { severity: Severity; className?: string }) {
  const meta = SEVERITY_META[severity];
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide",
        meta.badge,
        className,
      )}
    >
      {meta.label}
    </span>
  );
}

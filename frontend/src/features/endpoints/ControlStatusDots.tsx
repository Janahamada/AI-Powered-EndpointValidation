import { cn } from "@/lib/utils";
import { CONTROL_META, CONTROL_ORDER, STATUS_META } from "@/lib/constants";
import type { ControlType, ValidationStatus } from "@/types/api";

/** Compact per-control status indicator: one labelled dot per control. */
export function ControlStatusDots({
  statuses,
}: {
  statuses: Record<ControlType, ValidationStatus>;
}) {
  return (
    <div className="flex items-center gap-2">
      {CONTROL_ORDER.map((ct) => {
        const status = statuses[ct];
        if (!status) return null;
        const meta = CONTROL_META[ct];
        return (
          <span
            key={ct}
            title={`${meta.label}: ${STATUS_META[status].label}`}
            className="flex items-center gap-1 text-[11px] font-medium text-muted-foreground"
          >
            <span className={cn("size-2 rounded-full", STATUS_META[status].dot)} />
            {meta.short}
          </span>
        );
      })}
    </div>
  );
}

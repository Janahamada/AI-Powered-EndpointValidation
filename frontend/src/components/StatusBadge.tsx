import { CheckCircle2, AlertTriangle, XCircle, HelpCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { STATUS_META } from "@/lib/constants";
import type { ValidationStatus } from "@/types/api";

const ICONS = {
  PASS: CheckCircle2,
  WARNING: AlertTriangle,
  FAIL: XCircle,
  NO_DATA: HelpCircle,
} as const;

export function StatusBadge({
  status,
  className,
  showIcon = true,
}: {
  status: ValidationStatus;
  className?: string;
  showIcon?: boolean;
}) {
  const meta = STATUS_META[status];
  const Icon = ICONS[status];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold",
        meta.badge,
        className,
      )}
    >
      {showIcon && <Icon className="size-3.5" />}
      {meta.label}
    </span>
  );
}

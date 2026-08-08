import type { LucideIcon } from "lucide-react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function KpiCard({
  label,
  value,
  icon: Icon,
  tone = "default",
  hint,
}: {
  label: string;
  value: string | number;
  icon?: LucideIcon;
  tone?: "default" | "pass" | "warning" | "fail" | "primary";
  hint?: string;
}) {
  const toneClasses = {
    default: "text-foreground",
    primary: "text-primary",
    pass: "text-pass",
    warning: "text-warning",
    fail: "text-fail",
  }[tone];

  const iconBg = {
    default: "bg-muted text-muted-foreground",
    primary: "bg-primary/10 text-primary",
    pass: "bg-pass/10 text-pass",
    warning: "bg-warning/10 text-warning",
    fail: "bg-fail/10 text-fail",
  }[tone];

  return (
    <Card className="p-5">
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {label}
          </div>
          <div className={cn("mt-2 text-3xl font-bold tracking-tight", toneClasses)}>{value}</div>
          {hint && <div className="mt-1 text-xs text-muted-foreground">{hint}</div>}
        </div>
        {Icon && (
          <div className={cn("flex size-10 shrink-0 items-center justify-center rounded-lg", iconBg)}>
            <Icon className="size-5" />
          </div>
        )}
      </div>
    </Card>
  );
}

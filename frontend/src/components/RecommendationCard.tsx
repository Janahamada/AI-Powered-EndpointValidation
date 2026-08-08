import { ShieldCheck, BookMarked, Wrench, ArrowRight } from "lucide-react";
import { SeverityBadge } from "@/components/SeverityBadge";
import { CONTROL_META } from "@/lib/constants";
import { cn } from "@/lib/utils";
import type { Recommendation } from "@/types/api";

const ACCENT: Record<string, string> = {
  critical: "border-l-critical",
  high: "border-l-high",
  medium: "border-l-medium",
  low: "border-l-low",
};

/** One grounded remediation: finding → why → references → fix steps. */
export function RecommendationCard({ rec, index }: { rec: Recommendation; index: number }) {
  const control = CONTROL_META[rec.control_type];
  return (
    <div className={cn("rounded-lg border border-l-4 bg-card p-4", ACCENT[rec.severity])}>
      <div className="flex items-start gap-3">
        <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
          {index}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <SeverityBadge severity={rec.severity} />
            <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              {control.short}
            </span>
            <h4 className="font-semibold">{rec.title}</h4>
          </div>

          {/* Finding */}
          <p className="mt-1.5 text-sm text-muted-foreground">
            {rec.finding}{" "}
            <span className="text-foreground/70">
              (observed <span className="font-medium text-fail">{rec.observed}</span>, required{" "}
              <span className="font-medium text-pass">{rec.required}</span>)
            </span>
          </p>

          {/* Why */}
          <p className="mt-2 text-sm leading-relaxed">{rec.why}</p>

          {/* References */}
          <div className="mt-3 flex flex-wrap gap-2">
            <ReferenceChip icon={ShieldCheck} label={rec.policy_reference} tone="primary" />
            {rec.cis && (
              <ReferenceChip
                icon={BookMarked}
                label={`CIS ${rec.cis.safeguard} (${rec.cis.function}): ${rec.cis.title}`}
                tone="muted"
              />
            )}
          </div>

          {/* Remediation steps */}
          <div className="mt-3 rounded-md bg-muted/50 p-3">
            <div className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              <Wrench className="size-3.5" /> How to fix
            </div>
            <ul className="space-y-1">
              {rec.steps.map((step, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <ArrowRight className="mt-0.5 size-3.5 shrink-0 text-primary" />
                  <span>{step}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

function ReferenceChip({
  icon: Icon,
  label,
  tone,
}: {
  icon: typeof ShieldCheck;
  label: string;
  tone: "primary" | "muted";
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs font-medium",
        tone === "primary"
          ? "border-primary/25 bg-primary/10 text-primary"
          : "border-border bg-muted text-muted-foreground",
      )}
    >
      <Icon className="size-3.5 shrink-0" />
      {label}
    </span>
  );
}

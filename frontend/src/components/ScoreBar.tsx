import { cn } from "@/lib/utils";

/** Compliance-score bar, colored by band (green / amber / red). */
export function ScoreBar({
  score,
  className,
  showLabel = true,
}: {
  score: number;
  className?: string;
  showLabel?: boolean;
}) {
  const tone = score >= 90 ? "bg-pass" : score >= 70 ? "bg-warning" : "bg-fail";
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
        <div
          className={cn("h-full rounded-full transition-all", tone)}
          style={{ width: `${Math.max(0, Math.min(100, score))}%` }}
        />
      </div>
      {showLabel && (
        <span className="w-12 shrink-0 text-right text-xs font-semibold tabular-nums">
          {score % 1 === 0 ? score : score.toFixed(1)}%
        </span>
      )}
    </div>
  );
}

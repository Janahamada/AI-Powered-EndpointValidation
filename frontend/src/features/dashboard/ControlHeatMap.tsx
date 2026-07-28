/**
 * Fleet control heat map.
 *
 * Every endpoint is one tile; every tile is split into the four controls. The
 * point is pattern recognition — a control that is red across the whole grid
 * is a systemic gap, a single dark tile is one broken machine.
 *
 * Read-only and purely presentational: it renders the same evaluated summaries
 * the endpoints table already serves (`control_statuses` per endpoint) and
 * computes nothing about compliance itself.
 */

import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LayoutGrid } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/StatusBadge";
import { Spinner, ErrorState } from "@/components/common";
import { CONTROL_META, STATUS_META } from "@/lib/constants";
import { apiErrorMessage } from "@/lib/api";
import { useEndpoints } from "@/hooks/queries";
import { cn } from "@/lib/utils";
import type { ControlType, EndpointSummary, ValidationStatus } from "@/types/api";

const CONTROL_ORDER: ControlType[] = ["antivirus", "edr", "dlp", "bitlocker"];
const STATUS_ORDER: ValidationStatus[] = ["PASS", "WARNING", "FAIL", "NO_DATA"];

/** Solid fills — the grid reads as colour, so the muted badge tints are too pale. */
const CELL_FILL: Record<ValidationStatus, string> = {
  PASS: "bg-pass",
  WARNING: "bg-warning",
  FAIL: "bg-fail",
  NO_DATA: "bg-nodata/50",
};

type Focus = "all" | ControlType;

export function ControlHeatMap() {
  const { data, isLoading, error } = useEndpoints({
    page_size: 200,
    sort: "hostname",
    order: "asc",
  });
  const [focus, setFocus] = useState<Focus>("all");
  const [hovered, setHovered] = useState<EndpointSummary | null>(null);
  const navigate = useNavigate();

  const endpoints = data?.items ?? [];

  // Counts for the legend: per-cell when showing all controls, per-endpoint
  // when focused on one.
  const counts = useMemo(() => {
    const acc: Record<string, number> = { PASS: 0, WARNING: 0, FAIL: 0, NO_DATA: 0 };
    for (const e of endpoints) {
      const controls = focus === "all" ? CONTROL_ORDER : [focus];
      for (const c of controls) {
        const s = e.control_statuses[c];
        if (s && s in acc) acc[s] += 1;
      }
    }
    return acc;
  }, [endpoints, focus]);

  const totalCells = Object.values(counts).reduce((a, b) => a + b, 0);

  return (
    <Card className="mt-4">
      <CardHeader className="flex-col items-start gap-3 space-y-0 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <LayoutGrid className="size-4 text-primary" /> Fleet Control Heat Map
          </CardTitle>
          <p className="mt-1 text-xs text-muted-foreground">
            One tile per endpoint, quartered by control. Hover to inspect, click to open.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-1 rounded-md border p-1">
          {(["all", ...CONTROL_ORDER] as Focus[]).map((f) => (
            <button
              key={f}
              onClick={() => setFocus(f)}
              className={cn(
                "rounded px-2.5 py-1 text-xs font-medium transition-colors",
                focus === f
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted",
              )}
            >
              {f === "all" ? "All controls" : CONTROL_META[f].short}
            </button>
          ))}
        </div>
      </CardHeader>

      <CardContent>
        {isLoading ? (
          <div className="flex justify-center py-10">
            <Spinner className="size-6" />
          </div>
        ) : error ? (
          <ErrorState message={apiErrorMessage(error, "Could not load the fleet heat map.")} />
        ) : (
          <>
            {/* Legend */}
            <div className="mb-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs">
              {STATUS_ORDER.map((s) => (
                <span key={s} className="flex items-center gap-1.5">
                  <span className={cn("size-3 rounded-sm", CELL_FILL[s])} />
                  <span className="text-muted-foreground">
                    {STATUS_META[s].label} —{" "}
                    <span className="font-medium text-foreground/80">{counts[s]}</span>
                    {totalCells > 0 && (
                      <span className="text-muted-foreground">
                        {" "}
                        ({Math.round((counts[s] / totalCells) * 100)}%)
                      </span>
                    )}
                  </span>
                </span>
              ))}
            </div>

            <div className="flex flex-col gap-4 lg:flex-row lg:items-start">
              {/* The grid */}
              <div
                className="flex flex-1 flex-wrap content-start items-start gap-1.5"
                onMouseLeave={() => setHovered(null)}
              >
                {endpoints.map((e) => (
                  <button
                    key={e.hostname}
                    onMouseEnter={() => setHovered(e)}
                    onFocus={() => setHovered(e)}
                    onClick={() => navigate(`/endpoints/${encodeURIComponent(e.hostname)}`)}
                    aria-label={`${e.hostname} — ${e.status}, ${e.compliance_score}%`}
                    className={cn(
                      "size-7 overflow-hidden rounded-sm ring-offset-1 ring-offset-background transition-transform hover:z-10 hover:scale-125 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                      hovered?.hostname === e.hostname && "ring-2 ring-primary",
                    )}
                  >
                    {focus === "all" ? (
                      <span className="grid size-full grid-cols-2 grid-rows-2">
                        {CONTROL_ORDER.map((c) => (
                          <span
                            key={c}
                            className={cn(
                              "block size-full",
                              CELL_FILL[e.control_statuses[c]],
                            )}
                          />
                        ))}
                      </span>
                    ) : (
                      <span
                        className={cn(
                          "block size-full",
                          CELL_FILL[e.control_statuses[focus]],
                        )}
                      />
                    )}
                  </button>
                ))}
              </div>

              {/* Inspector */}
              <div className="w-full shrink-0 lg:w-72">
                {hovered ? (
                  <div className="animate-fade-in rounded-lg border bg-muted/30 p-4">
                    <div className="truncate text-sm font-semibold">{hovered.hostname}</div>
                    <div className="mt-0.5 text-xs text-muted-foreground">
                      {hovered.ip_address} · {hovered.business_owner}
                    </div>
                    <div className="mt-3 flex items-baseline gap-2">
                      <span className="text-2xl font-bold tracking-tight">
                        {hovered.compliance_score}%
                      </span>
                      <StatusBadge status={hovered.status} />
                    </div>
                    <div className="mt-3 space-y-1.5">
                      {CONTROL_ORDER.map((c) => {
                        const s = hovered.control_statuses[c];
                        return (
                          <div key={c} className="flex items-center justify-between gap-2 text-xs">
                            <span className="flex items-center gap-1.5 text-muted-foreground">
                              <span className={cn("size-2.5 rounded-sm", CELL_FILL[s])} />
                              {CONTROL_META[c].short}
                            </span>
                            <span className={cn("font-medium", STATUS_META[s].text)}>
                              {STATUS_META[s].label}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                    <div className="mt-3 border-t pt-2 text-xs text-muted-foreground">
                      {hovered.total_findings} finding(s) — {hovered.critical_findings} critical,{" "}
                      {hovered.high_findings} high.
                    </div>
                    <div className="mt-2 text-xs text-primary">Click the tile to open →</div>
                  </div>
                ) : (
                  <div className="rounded-lg border border-dashed p-4 text-xs text-muted-foreground">
                    <div className="font-medium text-foreground/80">
                      {endpoints.length} endpoints · {totalCells} cells
                    </div>
                    <p className="mt-1.5 leading-relaxed">
                      Hover any tile for its detail. Each tile is quartered:{" "}
                      {CONTROL_ORDER.map((c) => CONTROL_META[c].short).join(", ")} in reading
                      order (top-left, top-right, bottom-left, bottom-right). Switch to a single control to spot a systemic gap.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

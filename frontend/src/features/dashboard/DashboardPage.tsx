import { Link } from "react-router-dom";
import { MonitorSmartphone, ShieldCheck, AlertTriangle, ShieldAlert, ArrowRight } from "lucide-react";
import { PageHeader, ErrorState, CenteredSpinner } from "@/components/common";
import { KpiCard } from "@/components/KpiCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/StatusBadge";
import { SeverityBadge } from "@/components/SeverityBadge";
import { ScoreBar } from "@/components/ScoreBar";
import { Database } from "lucide-react";
import { CONTROL_META } from "@/lib/constants";
import { apiErrorMessage } from "@/lib/api";
import { useDashboard, useCollectionStatus } from "@/hooks/queries";
import { SeverityDonut, TrendChart } from "./charts";
import type { ValidationStatus } from "@/types/api";

const STATUS_TILES: { key: ValidationStatus; label: string }[] = [
  { key: "PASS", label: "Passing" },
  { key: "WARNING", label: "Warning" },
  { key: "FAIL", label: "Failing" },
  { key: "NO_DATA", label: "No Data" },
];

export function DashboardPage() {
  const { data, isLoading, error } = useDashboard();
  const { data: collection } = useCollectionStatus();

  if (isLoading) return <CenteredSpinner />;
  if (error || !data)
    return <ErrorState message={apiErrorMessage(error, "Failed to load dashboard.")} />;

  return (
    <div>
      <PageHeader
        title="Assurance Dashboard"
        description="Fleet-wide endpoint security posture across all four controls."
      />

      {/* KPI row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Total Endpoints" value={data.total_endpoints} icon={MonitorSmartphone} tone="primary" />
        <KpiCard
          label="Overall Assurance"
          value={`${data.overall_compliance_score}%`}
          icon={ShieldCheck}
          tone={data.overall_compliance_score >= 90 ? "pass" : data.overall_compliance_score >= 70 ? "warning" : "fail"}
        />
        <KpiCard label="Critical Findings" value={data.critical_findings} icon={ShieldAlert} tone="fail" />
        <KpiCard label="High-Risk Findings" value={data.high_risk_findings} icon={AlertTriangle} tone="warning" />
      </div>

      {/* Charts row */}
      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Compliance Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <TrendChart data={data.trend} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Findings by Severity</CardTitle>
          </CardHeader>
          <CardContent>
            <SeverityDonut data={data.findings_by_severity} />
            <div className="mt-3 flex flex-wrap justify-center gap-2">
              {(["critical", "high", "medium", "low"] as const).map((s) => (
                <SeverityBadge key={s} severity={s} />
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Status breakdown + per-control */}
      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Endpoint Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {STATUS_TILES.map((t) => (
              <div key={t.key} className="flex items-center justify-between">
                <StatusBadge status={t.key} />
                <span className="text-lg font-semibold tabular-nums">
                  {data.endpoint_status_breakdown[t.key] ?? 0}
                </span>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Per-Control Compliance</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {data.per_control.map((pc) => {
              const meta = CONTROL_META[pc.control_type];
              const Icon = meta.icon;
              return (
                <div key={pc.control_type}>
                  <div className="mb-1.5 flex items-center justify-between text-sm">
                    <span className="flex items-center gap-2 font-medium">
                      <Icon className="size-4 text-muted-foreground" />
                      {meta.label}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {pc.pass_count} pass · {pc.warning_count} warn · {pc.fail_count} fail
                      {pc.no_data_count > 0 ? ` · ${pc.no_data_count} no-data` : ""}
                    </span>
                  </div>
                  <ScoreBar score={pc.compliance_rate} />
                </div>
              );
            })}
          </CardContent>
        </Card>
      </div>

      {/* Data collection (AI Assurance Agent) */}
      {collection && (
        <Card className="mt-4">
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle className="flex items-center gap-2">
              <Database className="size-4 text-primary" /> Data Collection
            </CardTitle>
            <span className="text-xs text-muted-foreground">
              Last collected {collection.last_collected ?? "—"} · {collection.blueprint_rules} blueprint rules
            </span>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
              {collection.sources.map((s) => (
                <div key={s.name} className="rounded-lg border p-3">
                  <div className="text-xs font-medium text-muted-foreground">{s.name}</div>
                  <div className="mt-1 text-xl font-bold tabular-nums">{s.records}</div>
                  <div className="text-[11px] text-muted-foreground">
                    {s.coverage != null ? `${s.coverage}% coverage` : "inventory"}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Top findings */}
      <Card className="mt-4">
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle>Top Findings</CardTitle>
          <Link
            to="/endpoints?status=FAIL"
            className="flex items-center gap-1 text-sm font-medium text-primary hover:underline"
          >
            View failing endpoints <ArrowRight className="size-3.5" />
          </Link>
        </CardHeader>
        <CardContent>
          {data.top_findings.length === 0 ? (
            <p className="py-4 text-center text-sm text-muted-foreground">
              No findings — the fleet is fully compliant.
            </p>
          ) : (
            <ul className="divide-y">
              {data.top_findings.map((f, i) => (
                <li key={i} className="flex items-center gap-3 py-2.5">
                  <SeverityBadge severity={f.severity} />
                  <span className="text-xs font-medium uppercase text-muted-foreground">
                    {CONTROL_META[f.control_type].short}
                  </span>
                  <span className="min-w-0 flex-1 truncate text-sm">{f.description}</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

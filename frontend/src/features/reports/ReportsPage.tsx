import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  FileText,
  FileSpreadsheet,
  Download,
  Loader2,
  ScrollText,
  LogIn,
  ShieldAlert,
  MessageSquareText,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { PageHeader, EmptyState } from "@/components/common";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { downloadReport } from "@/lib/endpoints-api";
import { apiErrorMessage } from "@/lib/api";
import { useAuditTrail } from "@/hooks/queries";

interface ReportDef {
  key: string;
  title: string;
  description: string;
  icon: LucideIcon;
  path: string;
  filename: string;
}

const REPORTS: ReportDef[] = [
  {
    key: "fleet",
    title: "Fleet Assurance Report",
    description:
      "Executive-summary PDF: overall score, per-control compliance, top findings across all endpoints.",
    icon: FileText,
    path: "/api/v1/reports/fleet.pdf",
    filename: "fleet_assurance_report.pdf",
  },
  {
    key: "findings",
    title: "Findings Export",
    description:
      "Detailed Excel workbook: every finding with severity, expected vs. actual, plus an endpoint summary sheet.",
    icon: FileSpreadsheet,
    path: "/api/v1/reports/findings.xlsx",
    filename: "findings_export.xlsx",
  },
];

const ACTION_META: Record<string, { label: string; icon: LucideIcon; className: string }> = {
  login: { label: "Login", icon: LogIn, className: "bg-pass/10 text-pass" },
  login_failed: { label: "Failed login", icon: ShieldAlert, className: "bg-fail/10 text-fail" },
  report_generated: { label: "Report generated", icon: FileText, className: "bg-primary/10 text-primary" },
  chat_query: { label: "AI query", icon: MessageSquareText, className: "bg-warning/10 text-warning" },
};

export function ReportsPage() {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  async function handle(def: ReportDef) {
    setBusy(def.key);
    setError(null);
    try {
      await downloadReport(def.path, def.filename);
      // The download is itself an audited action — refresh the trail below.
      queryClient.invalidateQueries({ queryKey: ["audit-trail"] });
    } catch (err) {
      setError(apiErrorMessage(err, "Report generation failed."));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div>
      <PageHeader
        title="Reports"
        description="Generate and download assurance reports for stakeholders and audit evidence."
      />

      {error && (
        <div className="mb-4 rounded-md border border-fail/30 bg-fail/10 px-3 py-2 text-sm text-fail">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {REPORTS.map((def) => {
          const Icon = def.icon;
          return (
            <Card key={def.key}>
              <CardContent className="flex flex-col gap-4 p-5">
                <div className="flex size-11 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Icon className="size-6" />
                </div>
                <div>
                  <h3 className="font-semibold">{def.title}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">{def.description}</p>
                </div>
                <Button
                  onClick={() => handle(def)}
                  disabled={busy === def.key}
                  className="mt-auto w-fit"
                >
                  {busy === def.key ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <Download className="size-4" />
                  )}
                  Download
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <p className="mt-6 text-sm text-muted-foreground">
        Per-endpoint PDF reports are available from each endpoint's detail page.
      </p>

      <AuditTrailCard />
    </div>
  );
}

/**
 * The DB stamps events with SQLite's UTC `current_timestamp`, which serialises
 * without a zone marker — JS would otherwise read it as local time. Treat a
 * zone-less value as UTC before formatting.
 */
function formatWhen(iso: string): string {
  const hasZone = /[zZ]|[+-]\d{2}:?\d{2}$/.test(iso);
  return new Date(hasZone ? iso : `${iso}Z`).toLocaleString();
}

/** Append-only activity log: who did what, and when. */
function AuditTrailCard() {
  const { data, isLoading } = useAuditTrail(25);

  return (
    <Card className="mt-6">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle className="flex items-center gap-2">
            <ScrollText className="size-4 text-primary" /> Audit Trail
          </CardTitle>
          <p className="mt-1 text-xs text-muted-foreground">
            Append-only record of logins, report generation and AI queries. Entries can be read but
            never edited or deleted.
          </p>
        </div>
        {data && (
          <span className="shrink-0 text-xs text-muted-foreground">
            {data.total} event{data.total === 1 ? "" : "s"} recorded
          </span>
        )}
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex justify-center py-6">
            <Loader2 className="size-5 animate-spin text-primary" />
          </div>
        ) : !data || data.events.length === 0 ? (
          <EmptyState
            title="No activity recorded yet."
            hint="Sign in, generate a report or ask the AI assistant a question."
          />
        ) : (
          <>
            <div className="mb-3 flex flex-wrap gap-2">
              {Object.entries(data.counts_by_action).map(([action, n]) => {
                const meta = ACTION_META[action];
                return (
                  <Badge key={action} className={meta?.className ?? ""}>
                    {meta?.label ?? action}: {n}
                  </Badge>
                );
              })}
            </div>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>When</TableHead>
                  <TableHead>User</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Detail</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.events.map((e) => {
                  const meta = ACTION_META[e.action];
                  const Icon = meta?.icon;
                  return (
                    <TableRow key={e.id}>
                      <TableCell className="whitespace-nowrap text-xs text-muted-foreground">
                        {formatWhen(e.occurred_at)}
                      </TableCell>
                      <TableCell className="text-sm font-medium">{e.username}</TableCell>
                      <TableCell>
                        <Badge className={meta?.className ?? ""}>
                          {Icon && <Icon className="size-3" />}
                          {meta?.label ?? e.action}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">{e.detail}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </>
        )}
      </CardContent>
    </Card>
  );
}

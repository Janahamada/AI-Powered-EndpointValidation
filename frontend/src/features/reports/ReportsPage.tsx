import { useState } from "react";
import { FileText, FileSpreadsheet, Download, Loader2 } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { PageHeader } from "@/components/common";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { downloadReport } from "@/lib/endpoints-api";
import { apiErrorMessage } from "@/lib/api";

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

export function ReportsPage() {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handle(def: ReportDef) {
    setBusy(def.key);
    setError(null);
    try {
      await downloadReport(def.path, def.filename);
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
    </div>
  );
}

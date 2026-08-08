import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Download, Sparkles, Server, User, Network, Cpu, Loader2 } from "lucide-react";
import { ErrorState, CenteredSpinner } from "@/components/common";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/StatusBadge";
import { ScoreBar } from "@/components/ScoreBar";
import { ControlCard } from "./ControlCard";
import { FindingGovernanceCard } from "./FindingGovernanceCard";
import { useEndpointDetail } from "@/hooks/queries";
import { apiErrorMessage } from "@/lib/api";
import { downloadReport, fetchEndpointAiRecommendations } from "@/lib/endpoints-api";

export function EndpointDetailPage() {
  const { hostname = "" } = useParams();
  const { data, isLoading, error } = useEndpointDetail(hostname);
  const [downloading, setDownloading] = useState(false);
  const [aiSummary, setAiSummary] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);

  async function generateAiRecommendations() {
    setAiLoading(true);
    setAiError(null);
    try {
      const res = await fetchEndpointAiRecommendations(hostname);
      setAiSummary(
        res.ai_recommendations ??
          "The AI layer is offline; the grounded recommendations below are complete on their own.",
      );
    } catch (err) {
      setAiError(apiErrorMessage(err, "Could not generate the AI recommendations."));
    } finally {
      setAiLoading(false);
    }
  }

  async function handleDownload() {
    setDownloading(true);
    try {
      await downloadReport(
        `/api/v1/reports/endpoint/${encodeURIComponent(hostname)}.pdf`,
        `endpoint_report_${hostname}.pdf`,
      );
    } finally {
      setDownloading(false);
    }
  }

  if (isLoading) return <CenteredSpinner />;
  if (error || !data)
    return (
      <div className="space-y-4">
        <BackLink />
        <ErrorState message={apiErrorMessage(error, "Failed to load endpoint.")} />
      </div>
    );

  const { asset } = data;

  return (
    <div>
      <BackLink />

      {/* Header */}
      <div className="mb-6 mt-3 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight">{asset.hostname}</h1>
            <StatusBadge status={data.status} />
          </div>
          <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-sm text-muted-foreground">
            <span className="flex items-center gap-1.5"><Network className="size-4" />{asset.ip_address}</span>
            <span className="flex items-center gap-1.5"><Cpu className="size-4" />{asset.operating_system}</span>
            <span className="flex items-center gap-1.5"><User className="size-4" />{asset.business_owner}</span>
          </div>
        </div>
        <Button onClick={handleDownload} disabled={downloading} variant="outline">
          {downloading ? <Loader2 className="size-4 animate-spin" /> : <Download className="size-4" />}
          Download PDF report
        </Button>
      </div>

      {/* Score summary */}
      <Card className="mb-4">
        <CardContent className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <Server className="size-5 text-primary" />
            <div>
              <div className="text-sm text-muted-foreground">Overall compliance score</div>
              <div className="text-2xl font-bold">{data.compliance_score}%</div>
            </div>
          </div>
          <div className="w-full sm:w-72">
            <ScoreBar score={data.compliance_score} showLabel={false} />
          </div>
        </CardContent>
      </Card>

      {/* Control cards */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {data.controls.map((c) => (
          <ControlCard key={c.control_type} control={c} evidence={data.evidence} />
        ))}
      </div>

      {/* Findings lifecycle + evidence provenance */}
      <FindingGovernanceCard
        hostname={hostname}
        findings={data.findings}
        evidence={data.evidence}
      />

      {/* Recommendations */}
      <Card className="mt-4">
        <CardHeader className="flex-row items-center gap-2 space-y-0">
          <Sparkles className="size-5 text-primary" />
          <CardTitle>Recommendations</CardTitle>
          <span className="ml-auto rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
            Grounded in blueprint · policy · CIS
          </span>
        </CardHeader>
        <CardContent>
          {data.findings.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              This endpoint meets every blueprint rule — no remediation required.
            </p>
          ) : (
            <>
              {/* On-demand RAG-grounded AI recommendations */}
              <div className="mb-4">
                {aiSummary ? (
                  <div className="rounded-lg border border-primary/25 bg-primary/5 p-3">
                    <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-primary">
                      AI recommendations · retrieved from policy &amp; CIS docs (RAG)
                    </div>
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">{aiSummary}</p>
                  </div>
                ) : (
                  <div className="flex items-center gap-3">
                    <Button variant="outline" size="sm" onClick={generateAiRecommendations} disabled={aiLoading}>
                      {aiLoading ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
                      {aiLoading ? "Reading policies…" : "Generate AI recommendations"}
                    </Button>
                    <span className="text-xs text-muted-foreground">
                      The AI reads your policy &amp; CIS documents and writes recommendations citing them.
                    </span>
                  </div>
                )}
                {aiError && <p className="mt-2 text-xs text-fail">{aiError}</p>}
              </div>

              <p className="text-xs text-muted-foreground">
                The specific gaps are listed in each control card above; the AI writes the
                remediation for them from your policy &amp; CIS documents.
              </p>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function BackLink() {
  return (
    <Link
      to="/endpoints"
      className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
    >
      <ArrowLeft className="size-4" /> Back to assets
    </Link>
  );
}

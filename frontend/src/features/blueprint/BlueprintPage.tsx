import { BookMarked, ShieldCheck, FileText, Layers } from "lucide-react";
import { PageHeader, ErrorState, CenteredSpinner } from "@/components/common";
import { KpiCard } from "@/components/KpiCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { SeverityBadge } from "@/components/SeverityBadge";
import { CONTROL_META, fieldLabel, formatEvidenceValue } from "@/lib/constants";
import { apiErrorMessage } from "@/lib/api";
import { useBlueprint } from "@/hooks/queries";
import type { ControlBlueprint } from "@/types/api";

export function BlueprintPage() {
  const { data, isLoading, error } = useBlueprint();

  if (isLoading) return <CenteredSpinner />;
  if (error || !data)
    return <ErrorState message={apiErrorMessage(error, "Failed to load the blueprint.")} />;

  return (
    <div>
      <PageHeader
        title="Assurance Blueprint"
        description="The baseline every endpoint is validated against — rules, golden images, policies and CIS mappings."
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <KpiCard label="Blueprint Rules" value={data.total_rules} icon={Layers} tone="primary" />
        <KpiCard label="Control Policies" value={data.policies.length} icon={FileText} />
        <KpiCard
          label="CIS Standard"
          value={`${data.standard_safeguards} safeguards`}
          icon={ShieldCheck}
          hint={`${data.standard_name} · ${data.standard_controls} controls`}
        />
      </div>

      {/* Per-control rule sets */}
      <div className="mt-4 space-y-4">
        {data.controls.map((c) => (
          <ControlBlueprintCard key={c.control_type} control={c} />
        ))}
      </div>

      {/* Internal policies */}
      <Card className="mt-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="size-4 text-primary" /> Control Policies (Antivirus & EDR)
          </CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {data.policies.map((p) => (
            <div key={p.id} className="rounded-lg border p-3">
              <div className="flex items-center gap-2">
                <span className="rounded bg-primary/10 px-1.5 py-0.5 text-xs font-semibold text-primary">
                  {p.id}
                </span>
                <span className="text-sm font-medium">{p.title}</span>
              </div>
              <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{p.text}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function ControlBlueprintCard({ control }: { control: ControlBlueprint }) {
  const meta = CONTROL_META[control.control_type];
  const Icon = meta.icon;
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2">
          <Icon className="size-5 text-primary" />
          {meta.label}
        </CardTitle>
        <span className="text-xs text-muted-foreground">{control.rule_count} rules</span>
      </CardHeader>
      <CardContent>
        {/* Golden image reference (firewall / bitlocker) */}
        {control.golden_image && (
          <div className="mb-3 rounded-lg border border-primary/25 bg-primary/5 p-3">
            <div className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-primary">
              <BookMarked className="size-3.5" /> Golden image · {control.golden_image.reference}
            </div>
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
              {Object.entries(control.golden_image)
                .filter(([k]) => k !== "reference")
                .map(([k, v]) => (
                  <span key={k}>
                    <span className="text-muted-foreground">{k}:</span>{" "}
                    <span className="font-medium">{v}</span>
                  </span>
                ))}
            </div>
          </div>
        )}

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Requirement</TableHead>
              <TableHead>Severity</TableHead>
              <TableHead>Policy reference</TableHead>
              <TableHead>CIS safeguard</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {control.rules.map((r) => (
              <TableRow key={r.field}>
                <TableCell>
                  <div className="font-medium">{fieldLabel(r.field)}</div>
                  <div className="text-xs text-muted-foreground">
                    {r.operator_label}{" "}
                    <span className="font-medium text-foreground/80">
                      {formatEvidenceValue(r.expected)}
                    </span>
                  </div>
                </TableCell>
                <TableCell>
                  <SeverityBadge severity={r.severity} />
                </TableCell>
                <TableCell className="text-xs text-muted-foreground">{r.policy_reference}</TableCell>
                <TableCell className="text-xs">
                  {r.cis ? (
                    <span className="text-muted-foreground">
                      <span className="font-medium text-foreground/80">CIS {r.cis.safeguard}</span>{" "}
                      ({r.cis.function})
                    </span>
                  ) : (
                    "—"
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

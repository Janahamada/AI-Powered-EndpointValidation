import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/StatusBadge";
import { SeverityBadge } from "@/components/SeverityBadge";
import { cn } from "@/lib/utils";
import {
  CONTROL_META,
  EVIDENCE_FIELDS,
  fieldLabel,
  formatEvidenceValue,
} from "@/lib/constants";
import type { ControlRecord, ControlValidation } from "@/types/api";

export function ControlCard({
  control,
  evidence,
}: {
  control: ControlValidation;
  evidence: ControlRecord;
}) {
  const meta = CONTROL_META[control.control_type];
  const Icon = meta.icon;
  const failedFields = new Set(control.findings.map((f) => f.field));

  return (
    <Card className="overflow-hidden">
      <div className="flex items-center gap-3 border-b p-4">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Icon className="size-5" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="truncate font-semibold">{meta.label}</div>
          <div className="text-xs text-muted-foreground">
            {control.passed_fields}/{control.total_fields} checks passed · {control.score}%
          </div>
        </div>
        <StatusBadge status={control.status} />
      </div>

      <div className="p-4">
        {/* Evidence grid */}
        {control.present ? (
          <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            {EVIDENCE_FIELDS[control.control_type].map((field) => {
              const bad = failedFields.has(field);
              return (
                <div key={field} className="flex flex-col">
                  <dt className="text-xs text-muted-foreground">{fieldLabel(field)}</dt>
                  <dd className={cn("font-medium", bad && "text-fail")}>
                    {formatEvidenceValue(evidence[field])}
                  </dd>
                </div>
              );
            })}
          </dl>
        ) : (
          <p className="text-sm text-muted-foreground">
            No {meta.label} evidence is on file for this endpoint.
          </p>
        )}

        {/* Findings */}
        {control.findings.length > 0 && (
          <div className="mt-4 space-y-2 border-t pt-3">
            {control.findings.map((f, i) => (
              <div key={i} className="flex items-start gap-2 text-sm">
                <SeverityBadge severity={f.severity} className="mt-0.5" />
                <div className="min-w-0">
                  <span>{f.description}</span>
                  <span className="ml-1 text-xs text-muted-foreground">
                    (expected {formatEvidenceValue(f.expected)}, found {formatEvidenceValue(f.actual)})
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
}

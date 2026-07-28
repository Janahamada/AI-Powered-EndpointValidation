/**
 * Findings & recommendations — the governance layer over the rules engine.
 *
 * The engine decides what is *wrong*; this card records what the organisation
 * decided to *do* about it: remediate, tolerate as accepted risk (with a
 * justification and an expiry), or dispute as a false positive.
 *
 * Recommendations are deliberately kept out of scoring — a risk acceptance never
 * makes a failing control look like it passes. The card says so on screen.
 *
 * It also carries evidence provenance: for each finding, the source file the
 * value was ingested from and when it was loaded.
 */

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  CircleDot,
  FileInput,
  Loader2,
  ShieldQuestion,
  Timer,
  Undo2,
  Wrench,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SeverityBadge } from "@/components/SeverityBadge";
import { Spinner } from "@/components/common";
import { CONTROL_META, fieldLabel, formatEvidenceValue } from "@/lib/constants";
import { apiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useEvidenceSources, useFindingStates } from "@/hooks/queries";
import { clearFindingState, setFindingState } from "@/lib/endpoints-api";
import type {
  ControlRecord,
  EvidenceSource,
  Finding,
  FindingState,
  FindingStatus,
} from "@/types/api";

const STATUS_META: Record<
  FindingStatus | "open",
  { label: string; className: string; icon: typeof CircleDot }
> = {
  open: { label: "Open", className: "bg-muted text-muted-foreground", icon: CircleDot },
  in_progress: { label: "In progress", className: "bg-warning/15 text-warning", icon: Wrench },
  risk_accepted: { label: "Risk accepted", className: "bg-primary/10 text-primary", icon: ShieldQuestion },
  false_positive: { label: "False positive", className: "bg-nodata/15 text-nodata", icon: Undo2 },
};

const key = (controlType: string, field: string) => `${controlType}::${field}`;

export function FindingGovernanceCard({
  hostname,
  findings,
  evidence,
}: {
  hostname: string;
  findings: Finding[];
  evidence: ControlRecord;
}) {
  const { data: states, isLoading } = useFindingStates(hostname);
  const { data: provenance } = useEvidenceSources(hostname);
  const [editing, setEditing] = useState<string | null>(null);

  if (findings.length === 0) return null;

  const byKey = new Map((states ?? []).map((s) => [key(s.control_type, s.field), s]));
  const sourceByControl = new Map(
    (provenance?.sources ?? []).map((s) => [s.control_type, s]),
  );

  const tally: Record<string, number> = { open: 0, in_progress: 0, risk_accepted: 0, false_positive: 0 };
  for (const f of findings) {
    const s = byKey.get(key(f.control_type, f.field));
    // An expired acceptance is open again — that's the whole point of an expiry.
    tally[s && !s.expired ? s.status : "open"] += 1;
  }

  return (
    <Card className="mt-4">
      <CardHeader className="flex-col items-start gap-2 space-y-0 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <ShieldQuestion className="size-4 text-primary" /> Findings &amp; Recommendations
          </CardTitle>
          <p className="mt-1 text-xs text-muted-foreground">
            The agreed course of action for each finding. Recommendations are governance records —
            they never change the compliance score or status.
          </p>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {(Object.keys(tally) as (FindingStatus | "open")[])
            .filter((k) => tally[k] > 0)
            .map((k) => (
              <Badge key={k} className={STATUS_META[k].className}>
                {STATUS_META[k].label}: {tally[k]}
              </Badge>
            ))}
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex justify-center py-6">
            <Spinner />
          </div>
        ) : (
          <ul className="divide-y">
            {findings.map((f) => (
              <FindingRow
                key={key(f.control_type, f.field)}
                hostname={hostname}
                finding={f}
                state={byKey.get(key(f.control_type, f.field))}
                source={sourceByControl.get(f.control_type)}
                evidence={evidence}
                editing={editing === key(f.control_type, f.field)}
                onEdit={(open) => setEditing(open ? key(f.control_type, f.field) : null)}
              />
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

function FindingRow({
  hostname,
  finding,
  state,
  source,
  evidence,
  editing,
  onEdit,
}: {
  hostname: string;
  finding: Finding;
  state?: FindingState;
  source?: EvidenceSource;
  evidence: ControlRecord;
  editing: boolean;
  onEdit: (open: boolean) => void;
}) {
  const queryClient = useQueryClient();
  const [showEvidence, setShowEvidence] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const effective: FindingStatus | "open" = state && !state.expired ? state.status : "open";
  const meta = STATUS_META[effective];
  const Icon = meta.icon;

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["finding-states", hostname] });
    queryClient.invalidateQueries({ queryKey: ["audit-trail"] });
  };

  const save = useMutation({
    mutationFn: setFindingState,
    onSuccess: () => {
      setError(null);
      onEdit(false);
      invalidate();
    },
    onError: (e) => setError(apiErrorMessage(e, "Could not save the recommendation.")),
  });

  const remove = useMutation({
    mutationFn: () => clearFindingState(hostname, finding.control_type, finding.field),
    onSuccess: () => {
      onEdit(false);
      invalidate();
    },
  });

  // Raw ingested value for this finding's field, straight off the evidence row.
  const rawValue = (evidence as unknown as Record<string, unknown>)[finding.field];

  return (
    <li className="py-3">
      <div className="flex flex-wrap items-start gap-2">
        <SeverityBadge severity={finding.severity} />
        <span className="text-xs font-medium uppercase text-muted-foreground">
          {CONTROL_META[finding.control_type].short}
        </span>
        <div className="min-w-0 flex-1">
          <div className="text-sm font-medium">{fieldLabel(finding.field)}</div>
          <p className="text-xs text-muted-foreground">{finding.description}</p>
        </div>
        <Badge className={cn("gap-1", meta.className)}>
          <Icon className="size-3" />
          {meta.label}
        </Badge>
      </div>

      {state?.expired && (
        <div className="mt-2 flex items-center gap-1.5 rounded-md border border-warning/30 bg-warning/10 px-2 py-1 text-xs text-warning">
          <Timer className="size-3.5" />
          Risk acceptance expired on {new Date(state.expires_at!).toLocaleDateString()} — this
          finding is open again.
        </div>
      )}

      {state && !state.expired && (
        <div className="mt-2 rounded-md border bg-muted/30 p-2 text-xs">
          {state.justification && <p className="italic">“{state.justification}”</p>}
          <p className="mt-1 text-muted-foreground">
            {state.owner && <>Owner: {state.owner} · </>}
            {state.expires_at && <>Until {new Date(state.expires_at).toLocaleDateString()} · </>}
            Recorded by {state.updated_by} on {new Date(state.updated_at).toLocaleDateString()}
          </p>
        </div>
      )}

      <div className="mt-2 flex flex-wrap items-center gap-3 text-xs">
        <button
          onClick={() => onEdit(!editing)}
          className="font-medium text-primary hover:underline"
        >
          {editing ? "Cancel" : state ? "Change recommendation" : "Record recommendation"}
        </button>
        {state && (
          <button
            onClick={() => remove.mutate()}
            className="text-muted-foreground hover:text-fail hover:underline"
          >
            {remove.isPending ? "Reopening…" : "Reopen"}
          </button>
        )}
        <button
          onClick={() => setShowEvidence((v) => !v)}
          className="ml-auto inline-flex items-center gap-1 text-muted-foreground hover:text-foreground hover:underline"
        >
          <FileInput className="size-3" />
          {showEvidence ? "Hide evidence" : "Where did this come from?"}
        </button>
      </div>

      {/* Provenance drill-down */}
      {showEvidence && (
        <div className="animate-fade-in mt-2 rounded-md border border-dashed bg-muted/20 p-3 text-xs">
          <div className="grid gap-1.5 sm:grid-cols-2">
            <Row label="Field" value={finding.field} mono />
            <Row label="Observed value" value={formatEvidenceValue(rawValue)} mono />
            <Row label="Expected" value={formatEvidenceValue(finding.expected)} mono />
            <Row label="Source file" value={source?.source_file ?? "—"} mono />
            <Row
              label="Loaded at"
              value={source?.loaded_at ? new Date(source.loaded_at).toLocaleString() : "—"}
            />
            <Row label="Matched on" value={source?.key ?? hostname} mono />
          </div>
          <p className="mt-2 text-muted-foreground">
            The value above is the raw ingested evidence; the verdict comes from the blueprint rule
            for this field.
          </p>
        </div>
      )}

      {/* Recommendation form */}
      {editing && (
        <RecommendationForm
          hostname={hostname}
          finding={finding}
          existing={state}
          pending={save.isPending}
          error={error}
          onSubmit={(payload) => save.mutate(payload)}
        />
      )}
    </li>
  );
}

function Row({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex gap-2">
      <span className="w-28 shrink-0 text-muted-foreground">{label}</span>
      <span className={cn("min-w-0 break-words", mono && "font-mono")}>{value}</span>
    </div>
  );
}

function RecommendationForm({
  hostname,
  finding,
  existing,
  pending,
  error,
  onSubmit,
}: {
  hostname: string;
  finding: Finding;
  existing?: FindingState;
  pending: boolean;
  error: string | null;
  onSubmit: (payload: {
    hostname: string;
    control_type: string;
    field: string;
    status: FindingStatus;
    justification: string;
    owner: string;
    expires_at: string | null;
  }) => void;
}) {
  const [status, setStatus] = useState<FindingStatus>(existing?.status ?? "in_progress");
  const [justification, setJustification] = useState(existing?.justification ?? "");
  const [owner, setOwner] = useState(existing?.owner ?? "");
  const [expires, setExpires] = useState(existing?.expires_at?.slice(0, 10) ?? "");

  const needsJustification = status === "risk_accepted" || status === "false_positive";
  const needsExpiry = status === "risk_accepted";
  const invalid =
    (needsJustification && !justification.trim()) || (needsExpiry && !expires);

  return (
    <div className="animate-fade-in mt-3 rounded-lg border bg-muted/20 p-3">
      <div className="flex flex-wrap gap-1.5">
        {(["in_progress", "risk_accepted", "false_positive"] as FindingStatus[]).map((s) => (
          <button
            key={s}
            onClick={() => setStatus(s)}
            className={cn(
              "rounded px-2.5 py-1 text-xs font-medium transition-colors",
              status === s
                ? "bg-primary text-primary-foreground"
                : "bg-background text-muted-foreground hover:bg-muted",
            )}
          >
            {STATUS_META[s].label}
          </button>
        ))}
      </div>

      <div className="mt-3 grid gap-2 sm:grid-cols-2">
        <label className="text-xs">
          <span className="text-muted-foreground">Owner</span>
          <Input
            value={owner}
            onChange={(e) => setOwner(e.target.value)}
            placeholder="Who is accountable?"
            className="mt-1 h-8 text-xs"
          />
        </label>
        <label className="text-xs">
          <span className="text-muted-foreground">
            Expires {needsExpiry && <span className="text-fail">*</span>}
          </span>
          <Input
            type="date"
            value={expires}
            onChange={(e) => setExpires(e.target.value)}
            className="mt-1 h-8 text-xs"
          />
        </label>
      </div>

      <label className="mt-2 block text-xs">
        <span className="text-muted-foreground">
          Justification {needsJustification && <span className="text-fail">*</span>}
        </span>
        <textarea
          value={justification}
          onChange={(e) => setJustification(e.target.value)}
          rows={2}
          placeholder={
            status === "risk_accepted"
              ? "Why is this risk tolerable, and what compensates for it?"
              : "Why is this not a real finding?"
          }
          className="mt-1 w-full rounded-md border border-input bg-background px-2 py-1.5 text-xs shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
      </label>

      {needsExpiry && (
        <p className="mt-1.5 text-xs text-muted-foreground">
          Time-boxed by design: when the date passes, the finding reopens automatically.
        </p>
      )}
      {error && <p className="mt-2 text-xs text-fail">{error}</p>}

      <Button
        size="sm"
        className="mt-3"
        disabled={invalid || pending}
        onClick={() =>
          onSubmit({
            hostname,
            control_type: finding.control_type,
            field: finding.field,
            status,
            justification: justification.trim(),
            owner: owner.trim(),
            expires_at: expires ? `${expires}T00:00:00` : null,
          })
        }
      >
        {pending && <Loader2 className="size-4 animate-spin" />}
        Save recommendation
      </Button>
    </div>
  );
}

import { useEffect, useMemo, useState } from "react";
import {
  ChevronDown,
  ClipboardCheck,
  Layers,
  ListChecks,
  Radar,
  RotateCcw,
  Search,
  Settings2,
  Shield,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Zap,
} from "lucide-react";
import { PageHeader, EmptyState } from "@/components/common";
import { KpiCard } from "@/components/KpiCard";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { CONTROL_META } from "@/lib/constants";
import { cn } from "@/lib/utils";
import {
  ACCENTS,
  LIVE_CONTROLS,
  OUTCOMES,
  SECURITY_DOMAINS,
  TOTAL_CONTROLS,
  VALIDATION_STAGES,
  type SecurityDomain,
} from "./blueprint-domains";

type StatusFilter = "all" | "live" | "roadmap";

const OUTCOME_ICONS = [Shield, Radar, Zap, RotateCcw];
const STAGE_ICONS = [ClipboardCheck, Settings2, TrendingUp, ListChecks];

/** Eases a number up from zero on mount — purely cosmetic. */
function useCountUp(target: number, duration = 900) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    let frame = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / duration);
      setValue(target * (1 - Math.pow(1 - p, 3)));
      if (p < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target, duration]);
  return value;
}

export function SecurityBlueprintPage() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<StatusFilter>("all");
  // Domains that already have live coverage start open; the rest stay tidy.
  const [open, setOpen] = useState<string[]>(
    SECURITY_DOMAINS.filter((d) => d.controls.some((c) => c.validatedBy)).map((d) => d.slug),
  );
  const [activeStage, setActiveStage] = useState(1);

  const coverage = (LIVE_CONTROLS / TOTAL_CONTROLS) * 100;
  const animatedCoverage = useCountUp(coverage);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return SECURITY_DOMAINS.map((domain) => ({
      ...domain,
      controls: domain.controls.filter((c) => {
        if (status === "live" && !c.validatedBy) return false;
        if (status === "roadmap" && c.validatedBy) return false;
        if (!q) return true;
        return (
          c.name.toLowerCase().includes(q) ||
          domain.name.toLowerCase().includes(q) ||
          domain.objective.toLowerCase().includes(q)
        );
      }),
    })).filter((d) => d.controls.length > 0);
  }, [query, status]);

  const shown = filtered.reduce((n, d) => n + d.controls.length, 0);
  const allOpen = filtered.length > 0 && filtered.every((d) => open.includes(d.slug));

  const toggle = (slug: string) =>
    setOpen((o) => (o.includes(slug) ? o.filter((s) => s !== slug) : [...o, slug]));

  return (
    <div>
      <PageHeader
        title="Blueprint"
        description="Security controls across key domains ensure the Confidentiality, Integrity and Availability (CIA) of information."
      />

      {/* Tagline + CIA triad */}
      <Card className="mb-4 overflow-hidden">
        <div className="flex flex-col gap-4 bg-primary/5 p-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-primary">
              <Sparkles className="size-3.5" /> 10 Security Control Domains
            </div>
            <h2 className="mt-1.5 text-lg font-semibold tracking-tight">
              Ten domains. One standard of proof.
            </h2>
            <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
              Every control below is held to the same four questions — designed, implemented,
              operating, compliant. This page is the map; the rest of the platform is the evidence.
            </p>
          </div>
          <div className="flex shrink-0 gap-2">
            {[
              { label: "Confidentiality", cls: "text-sky-600 dark:text-sky-400 bg-sky-500/10" },
              { label: "Integrity", cls: "text-emerald-600 dark:text-emerald-400 bg-emerald-500/10" },
              { label: "Availability", cls: "text-amber-600 dark:text-amber-400 bg-amber-500/10" },
            ].map((t) => (
              <div
                key={t.label}
                className={cn(
                  "rounded-lg px-3 py-2 text-center text-[11px] font-semibold uppercase tracking-wide",
                  t.cls,
                )}
              >
                {t.label.slice(0, 1)}
                <div className="mt-0.5 text-[10px] font-medium normal-case tracking-normal opacity-80">
                  {t.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* KPIs */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Control Domains" value={SECURITY_DOMAINS.length} icon={Layers} tone="primary" />
        <KpiCard label="Blueprint Controls" value={TOTAL_CONTROLS} icon={ListChecks} />
        <KpiCard
          label="Validated Today"
          value={LIVE_CONTROLS}
          icon={ShieldCheck}
          tone="pass"
          hint="Evidence collected & rule-checked"
        />
        <KpiCard
          label="Blueprint Coverage"
          value={`${animatedCoverage.toFixed(1)}%`}
          icon={TrendingUp}
          tone="warning"
          hint={`${TOTAL_CONTROLS - LIVE_CONTROLS} controls on the roadmap`}
        />
      </div>

      {/* Coverage bar */}
      <Card className="mt-4 p-5">
        <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
          <span className="text-sm font-medium">Assurance coverage of the blueprint</span>
          <span className="text-xs text-muted-foreground">
            {LIVE_CONTROLS} live · {TOTAL_CONTROLS - LIVE_CONTROLS} planned
          </span>
        </div>
        <div className="h-2.5 w-full overflow-hidden rounded-full bg-muted">
          <div
            className="h-full rounded-full bg-pass transition-[width] duration-1000 ease-out"
            style={{ width: `${animatedCoverage}%` }}
          />
        </div>
        <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
          <span className="font-medium text-foreground/80">What&apos;s next:</span> the platform
          validates Endpoint and Data Security end-to-end today. Every remaining domain is already
          mapped here — each one lights up the moment its collector starts sending evidence.
        </p>
      </Card>

      {/* Toolbar */}
      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search controls, domains or objectives…"
            className="pl-9"
          />
        </div>
        <div className="flex items-center gap-1 rounded-md border p-1">
          {(
            [
              ["all", "All"],
              ["live", "Live now"],
              ["roadmap", "Roadmap"],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setStatus(key)}
              className={cn(
                "rounded px-3 py-1 text-xs font-medium transition-colors",
                status === key
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted",
              )}
            >
              {label}
            </button>
          ))}
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setOpen(allOpen ? [] : filtered.map((d) => d.slug))}
        >
          {allOpen ? "Collapse all" : "Expand all"}
        </Button>
      </div>

      <div className="mt-2 text-xs text-muted-foreground">
        Showing {shown} of {TOTAL_CONTROLS} controls across {filtered.length} domain(s).
      </div>

      {/* Domain tables */}
      <div className="mt-4 space-y-3">
        {filtered.length === 0 ? (
          <EmptyState title="No controls match that search." hint="Try a different term or clear the filter." />
        ) : (
          filtered.map((domain) => (
            <DomainCard
              key={domain.slug}
              domain={domain}
              expanded={open.includes(domain.slug)}
              onToggle={() => toggle(domain.slug)}
            />
          ))
        )}
      </div>

      {/* Validation stages */}
      <Card className="mt-6 p-5">
        <div className="text-xs font-semibold uppercase tracking-wide text-primary">
          Blueprint assurance validation — for each security control we validate:
        </div>
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {VALIDATION_STAGES.map((stage, i) => {
            const Icon = STAGE_ICONS[i];
            const accent = ACCENTS[stage.accent];
            const active = activeStage === stage.step;
            return (
              <button
                key={stage.step}
                onMouseEnter={() => setActiveStage(stage.step)}
                onFocus={() => setActiveStage(stage.step)}
                onClick={() => setActiveStage(stage.step)}
                className={cn(
                  "rounded-lg border p-4 text-left transition-all duration-200",
                  active ? "ring-2 ring-offset-1 ring-offset-background shadow-sm" : "hover:bg-muted/50",
                  active && accent.ring,
                )}
              >
                <div className={cn("flex size-9 items-center justify-center rounded-lg", accent.bg)}>
                  <Icon className={cn("size-5", accent.text)} />
                </div>
                <div className="mt-3 text-sm font-semibold">
                  <span className={accent.text}>{stage.step}.</span> {stage.name}
                </div>
                <p
                  className={cn(
                    "mt-1 text-xs leading-relaxed transition-colors",
                    active ? "text-foreground/80" : "text-muted-foreground",
                  )}
                >
                  {stage.question}
                </p>
              </button>
            );
          })}
        </div>
      </Card>

      {/* Key takeaway */}
      <Card className="mt-4 overflow-hidden">
        <div className="flex flex-col gap-4 bg-primary/5 p-5 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-start gap-3">
            <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
              <Sparkles className="size-5 text-primary" />
            </div>
            <div>
              <div className="text-xs font-semibold uppercase tracking-wide text-primary">
                Key takeaway
              </div>
              <p className="mt-1 max-w-3xl text-sm leading-relaxed">
                Cybersecurity Assurance is about validating that security controls across all
                domains are{" "}
                <span className="font-semibold text-foreground">properly designed, implemented,
                operating effectively, and compliant</span>{" "}
                to reduce risks and build confidence.
              </p>
            </div>
          </div>
          <div className="flex shrink-0 flex-wrap gap-2">
            {OUTCOMES.map((o, i) => {
              const Icon = OUTCOME_ICONS[i];
              return (
                <Badge key={o} variant="muted" className="gap-1.5 px-3 py-1">
                  <Icon className="size-3.5" />
                  {o}
                </Badge>
              );
            })}
          </div>
        </div>
      </Card>
    </div>
  );
}

function DomainCard({
  domain,
  expanded,
  onToggle,
}: {
  domain: SecurityDomain;
  expanded: boolean;
  onToggle: () => void;
}) {
  const accent = ACCENTS[domain.accent];
  const Icon = domain.icon;
  const live = domain.controls.filter((c) => c.validatedBy).length;
  const pct = Math.round((live / domain.controls.length) * 100);

  return (
    <Card className="overflow-hidden">
      <button
        onClick={onToggle}
        aria-expanded={expanded}
        className="flex w-full items-center gap-3 p-4 text-left transition-colors hover:bg-muted/40"
      >
        <div className={cn("flex size-10 shrink-0 items-center justify-center rounded-lg", accent.bg)}>
          <Icon className={cn("size-5", accent.text)} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className={cn("text-xs font-bold tabular-nums", accent.text)}>
              {String(domain.id).padStart(2, "0")}
            </span>
            <span className="text-sm font-semibold">{domain.name}</span>
            {live > 0 && (
              <Badge className="gap-1 bg-pass/10 text-pass">
                <ShieldCheck className="size-3" />
                {live} live
              </Badge>
            )}
          </div>
          <p className="mt-0.5 truncate text-xs text-muted-foreground">{domain.objective}</p>
        </div>
        <div className="hidden w-28 shrink-0 sm:block">
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
            <div
              className={cn("h-full rounded-full transition-all duration-700", accent.bar)}
              style={{ width: `${Math.max(pct, 2)}%` }}
            />
          </div>
          <div className="mt-1 text-right text-[10px] text-muted-foreground">
            {domain.controls.length} control{domain.controls.length === 1 ? "" : "s"}
          </div>
        </div>
        <ChevronDown
          className={cn(
            "size-4 shrink-0 text-muted-foreground transition-transform duration-200",
            expanded && "rotate-180",
          )}
        />
      </button>

      {expanded && (
        <CardContent className="animate-fade-in border-t pt-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Control</TableHead>
                <TableHead>Assurance status</TableHead>
                <TableHead>Validated by</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {domain.controls.map((c) => (
                <TableRow key={c.name}>
                  <TableCell className="font-medium">{c.name}</TableCell>
                  <TableCell>
                    {c.validatedBy ? (
                      <Badge className="gap-1 bg-pass/10 text-pass">
                        <ShieldCheck className="size-3" /> Live
                      </Badge>
                    ) : (
                      <Badge variant="muted">Planned</Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {c.validatedBy ? CONTROL_META[c.validatedBy].label : "Awaiting collector"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      )}
    </Card>
  );
}

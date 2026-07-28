import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  ChevronDown,
  ClipboardCheck,
  FlaskConical,
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

/** Stable identity for a catalogue entry, used as the simulation key. */
const simKey = (slug: string, control: string) => `${slug}::${control}`;

const OUTCOME_ICONS = [Shield, Radar, Zap, RotateCcw];
const STAGE_ICONS = [ClipboardCheck, Settings2, TrendingUp, ListChecks];

/**
 * Eases a number toward its target — from zero on mount, and from wherever it
 * currently sits whenever the target changes, so simulating a control makes
 * the figure climb rather than restart.
 */
function useCountUp(target: number, duration = 900) {
  const [value, setValue] = useState(0);
  const current = useRef(0);
  useEffect(() => {
    let frame = 0;
    const from = current.current;
    const start = performance.now();
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / duration);
      const next = from + (target - from) * (1 - Math.pow(1 - p, 3));
      current.current = next;
      setValue(next);
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
  // Planned controls the user is "what-if"-ing. Local state only: nothing is
  // persisted, sent anywhere, or mixed into the real coverage figures.
  const [simulated, setSimulated] = useState<Set<string>>(new Set());

  const baseCoverage = (LIVE_CONTROLS / TOTAL_CONTROLS) * 100;
  const effectiveLive = LIVE_CONTROLS + simulated.size;
  const coverage = (effectiveLive / TOTAL_CONTROLS) * 100;
  const animatedCoverage = useCountUp(coverage);
  const simulating = simulated.size > 0;

  const toggleSimulated = (key: string) =>
    setSimulated((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });

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
          value={simulating ? `${LIVE_CONTROLS} + ${simulated.size}` : LIVE_CONTROLS}
          icon={ShieldCheck}
          tone="pass"
          hint={
            simulating
              ? `${simulated.size} simulated, not yet collected`
              : "Evidence collected & rule-checked"
          }
        />
        <KpiCard
          label={simulating ? "Simulated Coverage" : "Blueprint Coverage"}
          value={`${animatedCoverage.toFixed(1)}%`}
          icon={TrendingUp}
          tone={simulating ? "primary" : "warning"}
          hint={
            simulating
              ? `Actual today is ${baseCoverage.toFixed(1)}%`
              : `${TOTAL_CONTROLS - LIVE_CONTROLS} controls on the roadmap`
          }
        />
      </div>

      {/* Coverage bar */}
      <Card className="mt-4 p-5">
        <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
          <span className="text-sm font-medium">Assurance coverage of the blueprint</span>
          <span className="text-xs text-muted-foreground">
            {LIVE_CONTROLS} live · {TOTAL_CONTROLS - effectiveLive} planned
            {simulating && <span className="text-primary"> · {simulated.size} simulated</span>}
          </span>
        </div>
        {/* Solid = actually validated, striped = simulated. */}
        <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-muted">
          <div
            className="h-full bg-pass transition-[width] duration-1000 ease-out"
            style={{ width: `${(LIVE_CONTROLS / TOTAL_CONTROLS) * 100}%` }}
          />
          <div
            className="h-full bg-primary/60 transition-[width] duration-500 ease-out"
            style={{
              width: `${Math.max(animatedCoverage - (LIVE_CONTROLS / TOTAL_CONTROLS) * 100, 0)}%`,
              backgroundImage:
                "repeating-linear-gradient(45deg, transparent, transparent 3px, rgba(255,255,255,.45) 3px, rgba(255,255,255,.45) 6px)",
            }}
          />
        </div>

        {simulating ? (
          <div className="mt-3 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-primary/30 bg-primary/5 p-3">
            <p className="text-xs leading-relaxed">
              <span className="font-semibold text-primary">Simulating {simulated.size} planned
              control{simulated.size === 1 ? "" : "s"}.</span>{" "}
              Coverage would rise from{" "}
              <span className="font-medium">{baseCoverage.toFixed(1)}%</span> to{" "}
              <span className="font-semibold text-primary">{coverage.toFixed(1)}%</span>. This is a
              projection only — no evidence is being collected for these.
            </p>
            <Button variant="outline" size="sm" onClick={() => setSimulated(new Set())}>
              <RotateCcw /> Reset
            </Button>
          </div>
        ) : (
          <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
            <span className="font-medium text-foreground/80">What&apos;s next:</span> the platform
            validates Endpoint and Data Security end-to-end today. Every remaining domain is already
            mapped here — tick any planned control below to model what adopting it would do to
            coverage.
          </p>
        )}
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
              simulated={simulated}
              onSimulate={toggleSimulated}
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
  simulated,
  onSimulate,
}: {
  domain: SecurityDomain;
  expanded: boolean;
  onToggle: () => void;
  simulated: Set<string>;
  onSimulate: (key: string) => void;
}) {
  const accent = ACCENTS[domain.accent];
  const Icon = domain.icon;
  const live = domain.controls.filter((c) => c.validatedBy).length;
  const simCount = domain.controls.filter((c) => simulated.has(simKey(domain.slug, c.name))).length;
  const pct = Math.round(((live + simCount) / domain.controls.length) * 100);
  const livePct = Math.round((live / domain.controls.length) * 100);

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
            {simCount > 0 && (
              <Badge className="gap-1 bg-primary/10 text-primary">
                <FlaskConical className="size-3" />+{simCount} simulated
              </Badge>
            )}
          </div>
          <p className="mt-0.5 truncate text-xs text-muted-foreground">{domain.objective}</p>
        </div>
        <div className="hidden w-28 shrink-0 sm:block">
          <div className="flex h-1.5 w-full overflow-hidden rounded-full bg-muted">
            <div
              className={cn("h-full transition-all duration-700", accent.bar)}
              style={{ width: `${Math.max(livePct, live ? 2 : 0)}%` }}
            />
            <div
              className="h-full bg-primary/50 transition-all duration-500"
              style={{ width: `${Math.max(pct - livePct, 0)}%` }}
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
                <TableHead className="text-right">Evidence</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {domain.controls.map((c) => {
                const key = simKey(domain.slug, c.name);
                const isSim = simulated.has(key);
                return (
                  <TableRow key={c.name}>
                    <TableCell className="font-medium">{c.name}</TableCell>
                    <TableCell>
                      {c.validatedBy ? (
                        <Badge className="gap-1 bg-pass/10 text-pass">
                          <ShieldCheck className="size-3" /> Live
                        </Badge>
                      ) : isSim ? (
                        <Badge className="gap-1 border-dashed border-primary/40 bg-primary/10 text-primary">
                          <FlaskConical className="size-3" /> Simulated
                        </Badge>
                      ) : (
                        <Badge variant="muted">Planned</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {c.validatedBy
                        ? CONTROL_META[c.validatedBy].label
                        : isSim
                          ? "Projected — no evidence collected"
                          : "Awaiting collector"}
                    </TableCell>
                    <TableCell className="text-right">
                      {c.validatedBy ? (
                        <Link
                          to={`/endpoints?control=${c.validatedBy}&control_status=FAIL`}
                          className="inline-flex items-center gap-1 whitespace-nowrap text-xs font-medium text-primary hover:underline"
                        >
                          Failing endpoints <ArrowRight className="size-3" />
                        </Link>
                      ) : (
                        <label className="inline-flex cursor-pointer items-center gap-1.5 whitespace-nowrap text-xs text-muted-foreground hover:text-foreground">
                          <input
                            type="checkbox"
                            checked={isSim}
                            onChange={() => onSimulate(key)}
                            className="size-3.5 cursor-pointer accent-primary"
                          />
                          Simulate
                        </label>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      )}
    </Card>
  );
}

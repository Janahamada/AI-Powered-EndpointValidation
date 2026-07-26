import {
  Area,
  AreaChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { SEVERITY_META, SEVERITY_ORDER } from "@/lib/constants";
import type { Severity, TrendPoint } from "@/types/api";

const tooltipStyle = {
  backgroundColor: "hsl(var(--card))",
  border: "1px solid hsl(var(--border))",
  borderRadius: "0.5rem",
  fontSize: "12px",
  color: "hsl(var(--foreground))",
};

export function SeverityDonut({ data }: { data: Record<Severity, number> }) {
  const slices = SEVERITY_ORDER.map((s) => ({
    name: SEVERITY_META[s].label,
    value: data[s] ?? 0,
    color: SEVERITY_META[s].color,
  })).filter((d) => d.value > 0);

  const total = slices.reduce((acc, d) => acc + d.value, 0);

  if (total === 0) {
    return (
      <div className="flex h-52 items-center justify-center text-sm text-muted-foreground">
        No open findings 🎉
      </div>
    );
  }

  return (
    <div className="relative h-52">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={slices}
            dataKey="value"
            nameKey="name"
            innerRadius={58}
            outerRadius={82}
            paddingAngle={2}
            stroke="none"
          >
            {slices.map((d) => (
              <Cell key={d.name} fill={d.color} />
            ))}
          </Pie>
          <Tooltip contentStyle={tooltipStyle} />
        </PieChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold tabular-nums">{total}</span>
        <span className="text-xs text-muted-foreground">findings</span>
      </div>
    </div>
  );
}

export function TrendChart({ data }: { data: TrendPoint[] }) {
  return (
    <div className="h-52">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 12, left: 4, bottom: 0 }}>
          <defs>
            <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.35} />
              <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            domain={[
              Math.max(0, Math.floor((Math.min(...data.map((d) => d.score)) - 5) / 5) * 5),
              100,
            ]}
            tickFormatter={(v: number) => `${Math.round(v)}%`}
            tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
            tickLine={false}
            axisLine={false}
            width={48}
          />
          <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => [`${v}%`, "Score"]} />
          <Area
            type="monotone"
            dataKey="score"
            stroke="hsl(var(--primary))"
            strokeWidth={2.5}
            fill="url(#trendFill)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

import { useMemo } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Search, ChevronLeft, ChevronRight, ArrowUpDown } from "lucide-react";
import { PageHeader, ErrorState, EmptyState, CenteredSpinner } from "@/components/common";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { StatusBadge } from "@/components/StatusBadge";
import { ScoreBar } from "@/components/ScoreBar";
import { ControlStatusDots } from "./ControlStatusDots";
import { useEndpoints, useEndpointFilters } from "@/hooks/queries";
import { apiErrorMessage } from "@/lib/api";
import type { EndpointQuery } from "@/lib/endpoints-api";

const PAGE_SIZE = 15;

export function EndpointsPage() {
  const [params, setParams] = useSearchParams();
  const { data: filters } = useEndpointFilters();

  const query: EndpointQuery = useMemo(
    () => ({
      q: params.get("q") ?? undefined,
      status: params.get("status") ?? undefined,
      owner: params.get("owner") ?? undefined,
      os: params.get("os") ?? undefined,
      sort: params.get("sort") ?? "hostname",
      order: (params.get("order") as "asc" | "desc") ?? "asc",
      page: Number(params.get("page") ?? 1),
      page_size: PAGE_SIZE,
    }),
    [params],
  );

  const { data, isLoading, error, isFetching } = useEndpoints(query);

  function update(patch: Record<string, string | undefined>, resetPage = true) {
    const next = new URLSearchParams(params);
    Object.entries(patch).forEach(([k, v]) => {
      if (v === undefined || v === "") next.delete(k);
      else next.set(k, v);
    });
    if (resetPage) next.set("page", "1");
    setParams(next, { replace: true });
  }

  function toggleSort(key: string) {
    const isActive = query.sort === key;
    const order = isActive && query.order === "asc" ? "desc" : "asc";
    update({ sort: key, order }, false);
  }

  const page = query.page ?? 1;
  const totalPages = data?.total_pages ?? 1;

  return (
    <div>
      <PageHeader
        title="Endpoints"
        description="Search, filter and drill into every endpoint's four-control validation."
      />

      {/* Filter bar */}
      <Card className="mb-4 p-3">
        <div className="flex flex-col gap-3 md:flex-row md:items-center">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search hostname, IP or owner…"
              className="pl-8"
              defaultValue={query.q ?? ""}
              onChange={(e) => update({ q: e.target.value })}
            />
          </div>
          <FilterSelect
            value={query.status ?? ""}
            onChange={(v) => update({ status: v })}
            placeholder="All statuses"
            options={(filters?.statuses ?? []).map((s) => ({ value: s, label: s }))}
          />
          <FilterSelect
            value={query.owner ?? ""}
            onChange={(v) => update({ owner: v })}
            placeholder="All owners"
            options={(filters?.owners ?? []).map((o) => ({ value: o, label: o }))}
          />
          <FilterSelect
            value={query.os ?? ""}
            onChange={(v) => update({ os: v })}
            placeholder="All OS"
            options={(filters?.operating_systems ?? []).map((o) => ({ value: o, label: o }))}
          />
        </div>
      </Card>

      {isLoading ? (
        <CenteredSpinner />
      ) : error ? (
        <ErrorState message={apiErrorMessage(error, "Failed to load endpoints.")} />
      ) : !data || data.items.length === 0 ? (
        <EmptyState title="No endpoints match your filters" hint="Try clearing the search or filters." />
      ) : (
        <Card className={isFetching ? "opacity-70 transition-opacity" : "transition-opacity"}>
          <Table>
            <TableHeader>
              <TableRow>
                <SortableHead label="Hostname" sortKey="hostname" query={query} onSort={toggleSort} />
                <TableHead>IP Address</TableHead>
                <TableHead>Owner</TableHead>
                <TableHead>Controls</TableHead>
                <SortableHead label="Status" sortKey="status" query={query} onSort={toggleSort} />
                <SortableHead label="Score" sortKey="score" query={query} onSort={toggleSort} className="w-40" />
                <SortableHead label="Critical" sortKey="critical" query={query} onSort={toggleSort} />
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.map((ep) => (
                <TableRow key={ep.hostname} className="cursor-pointer">
                  <TableCell className="font-medium">
                    <Link to={`/endpoints/${encodeURIComponent(ep.hostname)}`} className="hover:text-primary hover:underline">
                      {ep.hostname}
                    </Link>
                  </TableCell>
                  <TableCell className="tabular-nums text-muted-foreground">{ep.ip_address}</TableCell>
                  <TableCell className="text-muted-foreground">{ep.business_owner}</TableCell>
                  <TableCell>
                    <ControlStatusDots statuses={ep.control_statuses} />
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={ep.status} />
                  </TableCell>
                  <TableCell>
                    <ScoreBar score={ep.compliance_score} />
                  </TableCell>
                  <TableCell>
                    {ep.critical_findings > 0 ? (
                      <span className="font-semibold text-fail tabular-nums">{ep.critical_findings}</span>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {/* Pagination */}
          <div className="flex items-center justify-between border-t px-4 py-3 text-sm">
            <span className="text-muted-foreground">
              {data.total} endpoint{data.total === 1 ? "" : "s"} · page {page} of {totalPages}
            </span>
            <div className="flex gap-1">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => update({ page: String(page - 1) }, false)}
              >
                <ChevronLeft className="size-4" /> Prev
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => update({ page: String(page + 1) }, false)}
              >
                Next <ChevronRight className="size-4" />
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

function FilterSelect({
  value,
  onChange,
  placeholder,
  options,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
  options: { value: string; label: string }[];
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring md:w-40"
    >
      <option value="">{placeholder}</option>
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}

function SortableHead({
  label,
  sortKey,
  query,
  onSort,
  className,
}: {
  label: string;
  sortKey: string;
  query: EndpointQuery;
  onSort: (key: string) => void;
  className?: string;
}) {
  const active = query.sort === sortKey;
  return (
    <TableHead className={className}>
      <button
        onClick={() => onSort(sortKey)}
        className="inline-flex items-center gap-1 uppercase tracking-wide hover:text-foreground"
      >
        {label}
        <ArrowUpDown className={`size-3 ${active ? "text-primary" : "opacity-40"}`} />
      </button>
    </TableHead>
  );
}

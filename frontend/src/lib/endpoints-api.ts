import { api } from "./api";
import type {
  ChatResponse,
  DashboardSummary,
  EndpointDetail,
  EndpointFilters,
  PaginatedEndpoints,
  Token,
  User,
} from "@/types/api";

export async function login(username: string, password: string): Promise<Token> {
  const form = new URLSearchParams();
  form.set("username", username);
  form.set("password", password);
  const { data } = await api.post<Token>("/api/v1/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data;
}

export async function fetchMe(): Promise<User> {
  const { data } = await api.get<User>("/api/v1/auth/me");
  return data;
}

export async function fetchDashboard(): Promise<DashboardSummary> {
  const { data } = await api.get<DashboardSummary>("/api/v1/dashboard/summary");
  return data;
}

export interface EndpointQuery {
  q?: string;
  status?: string;
  owner?: string;
  os?: string;
  control?: string;
  control_status?: string;
  sort?: string;
  order?: "asc" | "desc";
  page?: number;
  page_size?: number;
}

export async function fetchEndpoints(params: EndpointQuery): Promise<PaginatedEndpoints> {
  const { data } = await api.get<PaginatedEndpoints>("/api/v1/endpoints", { params });
  return data;
}

export async function fetchEndpointFilters(): Promise<EndpointFilters> {
  const { data } = await api.get<EndpointFilters>("/api/v1/endpoints/filters");
  return data;
}

export async function fetchEndpointDetail(hostname: string): Promise<EndpointDetail> {
  const { data } = await api.get<EndpointDetail>(
    `/api/v1/endpoints/${encodeURIComponent(hostname)}`,
  );
  return data;
}

export async function sendChat(message: string): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>("/api/v1/chat", { message });
  return data;
}

export interface EndpointAiRecommendations {
  hostname: string;
  ai_recommendations: string | null;
  ai_available: boolean;
}

/** On-demand RAG-grounded recommendations for an endpoint: the model reads
 *  retrieved policy/CIS excerpts and writes remediation guidance citing them.
 *  Can take up to ~90s on a large model. */
export async function fetchEndpointAiRecommendations(
  hostname: string,
): Promise<EndpointAiRecommendations> {
  const { data } = await api.get<EndpointAiRecommendations>(
    `/api/v1/endpoints/${encodeURIComponent(hostname)}/recommendations`,
    { timeout: 130_000 }, // above the backend LLM timeout so it never cuts off early
  );
  return data;
}

export async function fetchAiStatus(): Promise<{ ollama_online: boolean; message: string }> {
  const { data } = await api.get("/api/v1/chat/status");
  return data;
}

export interface CollectionSource {
  name: string;
  source: string;
  records: number;
  coverage?: number;
}

export interface CollectionStatus {
  last_collected: string | null;
  sources: CollectionSource[];
  blueprint_rules: number;
  drift: Record<string, number | string[]>;
  total_endpoints: number;
}

export async function fetchCollectionStatus(): Promise<CollectionStatus> {
  const { data } = await api.get<CollectionStatus>("/api/v1/system/collection");
  return data;
}

export async function fetchBlueprint(): Promise<import("@/types/api").BlueprintView> {
  const { data } = await api.get("/api/v1/blueprint");
  return data;
}

/** Downloads a binary report and triggers a browser save. */
export async function downloadReport(path: string, filename: string): Promise<void> {
  const res = await api.get(path, { responseType: "blob" });
  const url = window.URL.createObjectURL(res.data as Blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

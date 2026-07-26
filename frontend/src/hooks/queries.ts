import { useQuery } from "@tanstack/react-query";
import {
  fetchAiStatus,
  fetchBlueprint,
  fetchCollectionStatus,
  fetchDashboard,
  fetchEndpointDetail,
  fetchEndpointFilters,
  fetchEndpoints,
  type EndpointQuery,
} from "@/lib/endpoints-api";

export function useDashboard() {
  return useQuery({ queryKey: ["dashboard"], queryFn: fetchDashboard });
}

export function useEndpoints(params: EndpointQuery) {
  return useQuery({
    queryKey: ["endpoints", params],
    queryFn: () => fetchEndpoints(params),
    placeholderData: (prev) => prev, // keep table stable while paging/filtering
  });
}

export function useEndpointFilters() {
  return useQuery({ queryKey: ["endpoint-filters"], queryFn: fetchEndpointFilters, staleTime: 300_000 });
}

export function useEndpointDetail(hostname: string) {
  return useQuery({
    queryKey: ["endpoint", hostname],
    queryFn: () => fetchEndpointDetail(hostname),
    enabled: !!hostname,
  });
}

export function useAiStatus() {
  return useQuery({ queryKey: ["ai-status"], queryFn: fetchAiStatus, staleTime: 60_000 });
}

export function useCollectionStatus() {
  return useQuery({ queryKey: ["collection-status"], queryFn: fetchCollectionStatus, staleTime: 120_000 });
}

export function useBlueprint() {
  return useQuery({ queryKey: ["blueprint"], queryFn: fetchBlueprint, staleTime: 300_000 });
}

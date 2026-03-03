import { useQuery } from "@tanstack/react-query";
import { fetchMetrics } from "../services/api";

export function useMetrics({ nodeId, metric, start, end, aggregation }, refetchInterval) {
  return useQuery({
    queryKey: ["metrics", nodeId, metric, start, end, aggregation],
    queryFn: () => fetchMetrics({ nodeId, metric, start, end, aggregation }),
    refetchInterval,
    enabled: !!start && !!end,
  });
}

import { useQuery } from "@tanstack/react-query";
import { fetchNodes } from "../services/api";

export function useNodeStatus(refetchInterval = 10_000) {
  return useQuery({
    queryKey: ["nodes"],
    queryFn: fetchNodes,
    refetchInterval,
  });
}

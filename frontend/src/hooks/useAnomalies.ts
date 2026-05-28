import { useQuery } from "@tanstack/react-query";
import { getAnomalies } from "../api/anomalies";

/** Fleet-wide recent anomalies, polled every 5 s. */
export function useAnomalies() {
  return useQuery({
    queryKey: ["anomalies"],
    queryFn: () => getAnomalies(),
    refetchInterval: 5000,
    staleTime: 3000,
  });
}

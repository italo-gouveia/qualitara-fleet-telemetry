import { useQuery } from "@tanstack/react-query";
import { getZoneCounts } from "../api/zones";

export function useZoneCounts() {
  return useQuery({
    queryKey: ["zoneCounts"],
    queryFn: getZoneCounts,
    refetchInterval: 2000,
    staleTime: 1000,
  });
}

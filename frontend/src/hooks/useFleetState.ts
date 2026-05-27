import { useQuery } from "@tanstack/react-query";
import { getFleetState } from "../api/vehicles";

export function useFleetState() {
  return useQuery({
    queryKey: ["fleetState"],
    queryFn: getFleetState,
    refetchInterval: 2000,
    staleTime: 1000,
  });
}

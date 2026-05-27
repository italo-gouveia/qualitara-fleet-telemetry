import { useQuery } from "@tanstack/react-query";
import { getAnomalies } from "../api/anomalies";

export function useVehicleAnomalies(vehicleId: string) {
  return useQuery({
    queryKey: ["anomalies", vehicleId],
    queryFn: () => getAnomalies(vehicleId),
    refetchInterval: 5000,
    staleTime: 3000,
  });
}

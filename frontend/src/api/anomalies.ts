import { apiFetch } from "./client";
import type { Anomaly } from "../types";

export const getAnomalies = (vehicleId?: string) =>
  apiFetch<Anomaly[]>("/anomalies", vehicleId ? { vehicle_id: vehicleId, limit: "5" } : { limit: "20" });

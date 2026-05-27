export type VehicleStatus = "idle" | "moving" | "charging" | "fault";

export interface Vehicle {
  vehicle_id: string;
  status: VehicleStatus;
  battery_pct: number;
  lat: number;
  lon: number;
  updated_at: string;
}

export interface Anomaly {
  id: number;
  vehicle_id: string;
  detected_at: string;
  type: string;
  detail: Record<string, unknown>;
}

export type ZoneCounts = Record<string, number>;

export interface FleetState {
  idle: number;
  moving: number;
  charging: number;
  fault: number;
  total: number;
}

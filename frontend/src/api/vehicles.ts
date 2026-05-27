import { apiFetch } from "./client";
import type { FleetState, Vehicle } from "../types";

export const getVehicles = () => apiFetch<Vehicle[]>("/vehicles");
export const getFleetState = () => apiFetch<FleetState>("/fleet/state");

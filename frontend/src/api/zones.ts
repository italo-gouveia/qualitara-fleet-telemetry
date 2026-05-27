import { apiFetch } from "./client";
import type { ZoneCounts } from "../types";

export const getZoneCounts = () => apiFetch<ZoneCounts>("/zones/counts");

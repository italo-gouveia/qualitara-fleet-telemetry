import { http, HttpResponse } from 'msw'

const BASE = 'http://localhost:8000'

export const handlers = [
  http.get(`${BASE}/fleet/state`, () =>
    HttpResponse.json({ idle: 10, moving: 5, charging: 3, fault: 1, total: 19 }),
  ),

  http.get(`${BASE}/vehicles`, () =>
    HttpResponse.json([
      {
        vehicle_id: 'v-01',
        status: 'moving',
        battery_pct: 75,
        lat: 51.505,
        lon: -0.09,
        updated_at: '2026-05-28T10:00:00Z',
      },
      {
        vehicle_id: 'v-02',
        status: 'fault',
        battery_pct: 8,
        lat: 51.506,
        lon: -0.091,
        updated_at: '2026-05-28T10:00:00Z',
      },
    ]),
  ),

  http.get(`${BASE}/zones/counts`, () =>
    HttpResponse.json({ aisle_a: 5, charging_bay_1: 12, pack_station: 3 }),
  ),

  http.get(`${BASE}/anomalies`, () => HttpResponse.json([])),
]

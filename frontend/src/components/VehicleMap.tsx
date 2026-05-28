import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { useVehicles } from "../hooks/useVehicles";
import { useAnomalies } from "../hooks/useAnomalies";
import type { VehicleStatus } from "../types";

const STATUS_COLOR: Record<VehicleStatus, string> = {
  moving: "#22c55e",
  charging: "#3b82f6",
  idle: "#64748b",
  fault: "#ef4444",
};

/** Approximate warehouse cluster centre (Mountain View, CA — matches simulator seed) */
const MAP_CENTER: [number, number] = [37.41, -122.08];

export function VehicleMap() {
  const { data: vehicles, isLoading, isError } = useVehicles();
  const { data: anomalies } = useAnomalies();

  /** Vehicles that have at least one recent anomaly in the current window */
  const vehiclesWithAnomaly = new Set(anomalies?.map((a) => a.vehicle_id) ?? []);

  if (isLoading) return <div className="panel"><p>Loading map…</p></div>;
  if (isError)   return <div className="panel"><p className="error">Failed to load vehicle positions.</p></div>;

  return (
    <div className="panel map-panel">
      <h2>
        Live Vehicle Map
        {(vehicles?.length ?? 0) > 0 && (
          <span className="panel-count">{vehicles!.length}</span>
        )}
      </h2>

      <MapContainer
        center={MAP_CENTER}
        zoom={14}
        style={{ height: "380px", borderRadius: "6px", zIndex: 0 }}
        scrollWheelZoom
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {vehicles?.map((v) => (
          <span key={v.vehicle_id}>
            {/* Anomaly pulse ring — outer transparent ring for vehicles with active anomalies */}
            {vehiclesWithAnomaly.has(v.vehicle_id) && (
              <CircleMarker
                center={[v.lat, v.lon]}
                radius={14}
                pathOptions={{
                  color: "#ef4444",
                  fillColor: "#ef4444",
                  fillOpacity: 0.12,
                  weight: 1.5,
                  dashArray: "3 2",
                }}
                interactive={false}
              />
            )}

            {/* Main marker */}
            <CircleMarker
              center={[v.lat, v.lon]}
              radius={7}
              pathOptions={{
                color: STATUS_COLOR[v.status],
                fillColor: STATUS_COLOR[v.status],
                fillOpacity: 0.9,
                weight: 2,
              }}
            >
              <Tooltip direction="top" offset={[0, -10]} opacity={0.95}>
                <strong>{v.vehicle_id}</strong> &middot; {v.status}
              </Tooltip>

              <Popup minWidth={160}>
                <div className="map-popup">
                  <p className="map-popup-id">{v.vehicle_id}</p>
                  <p>
                    Status: <strong>{v.status}</strong>
                  </p>
                  <p>Battery: <strong>{v.battery_pct}%</strong></p>
                  <p className="map-popup-coord">
                    {v.lat.toFixed(5)}, {v.lon.toFixed(5)}
                  </p>
                  {vehiclesWithAnomaly.has(v.vehicle_id) && (
                    <p className="map-popup-alert">⚠ Active anomaly</p>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          </span>
        ))}
      </MapContainer>

      {/* Status legend */}
      <div className="map-legend">
        {(["moving", "charging", "idle", "fault"] as VehicleStatus[]).map((s) => (
          <span key={s} className="legend-item">
            <span
              className="legend-dot"
              style={{ background: STATUS_COLOR[s] }}
            />
            {s}
          </span>
        ))}
        <span className="legend-item">
          <span className="legend-ring" />
          anomaly
        </span>
      </div>
    </div>
  );
}

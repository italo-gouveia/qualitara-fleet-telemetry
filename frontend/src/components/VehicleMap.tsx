import { useEffect } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip, useMap } from "react-leaflet";
import type { LatLngBoundsExpression } from "leaflet";
import "leaflet/dist/leaflet.css";
import { useVehicles } from "../hooks/useVehicles";
import { useAnomalies } from "../hooks/useAnomalies";
import type { Vehicle, VehicleStatus } from "../types";

const STATUS_COLOR: Record<VehicleStatus, string> = {
  moving: "#22c55e",
  charging: "#3b82f6",
  idle: "#64748b",
  fault: "#ef4444",
};

/** Fallback centre used only before data arrives */
const MAP_CENTER: [number, number] = [37.41, -122.08];

/**
 * Fits the map to encompass all vehicle positions on first load.
 * Does NOT re-fit on subsequent polls — avoids jumping while vehicles drift.
 */
function FitBounds({ vehicles }: { vehicles: Vehicle[] }) {
  const map = useMap();
  useEffect(() => {
    if (vehicles.length === 0) return;
    const bounds: LatLngBoundsExpression = vehicles.map((v) => [v.lat, v.lon]);
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 13 });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // intentionally runs once on mount only
  return null;
}

export function VehicleMap() {
  const { data: vehicles, isLoading, isError } = useVehicles();
  const { data: anomalies } = useAnomalies();

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
        zoom={10}
        style={{ height: "420px", borderRadius: "6px", zIndex: 0 }}
        scrollWheelZoom
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Auto-fit bounds to all vehicles on first render */}
        {vehicles && vehicles.length > 0 && <FitBounds vehicles={vehicles} />}

        {vehicles?.map((v) => (
          <span key={v.vehicle_id}>
            {/* Anomaly ring */}
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
                  <p>Status: <strong>{v.status}</strong></p>
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

      <div className="map-legend">
        {(["moving", "charging", "idle", "fault"] as VehicleStatus[]).map((s) => (
          <span key={s} className="legend-item">
            <span className="legend-dot" style={{ background: STATUS_COLOR[s] }} />
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

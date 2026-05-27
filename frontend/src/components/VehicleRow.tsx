import type { Vehicle } from "../types";
import { useVehicleAnomalies } from "../hooks/useVehicleAnomalies";

const STATUS_BADGE: Record<string, string> = {
  idle: "badge-slate",
  moving: "badge-blue",
  charging: "badge-green",
  fault: "badge-red",
};

interface Props {
  vehicle: Vehicle;
}

export function VehicleRow({ vehicle }: Props) {
  const { data: anomalies } = useVehicleAnomalies(vehicle.vehicle_id);
  const latest = anomalies?.[0];

  return (
    <tr className={vehicle.status === "fault" ? "row-fault" : ""}>
      <td>{vehicle.vehicle_id}</td>
      <td>
        <span className={`badge ${STATUS_BADGE[vehicle.status] ?? "badge-slate"}`}>
          {vehicle.status}
        </span>
      </td>
      <td>
        <div className="battery-bar">
          <div
            className="battery-fill"
            style={{
              width: `${vehicle.battery_pct}%`,
              backgroundColor: vehicle.battery_pct < 15 ? "#ef4444" : "#22c55e",
            }}
          />
        </div>
        <span>{vehicle.battery_pct}%</span>
      </td>
      <td>
        {latest && (
          <span className="badge badge-orange">{latest.type}</span>
        )}
      </td>
      <td className="coord">
        {vehicle.lat.toFixed(4)}, {vehicle.lon.toFixed(4)}
      </td>
    </tr>
  );
}

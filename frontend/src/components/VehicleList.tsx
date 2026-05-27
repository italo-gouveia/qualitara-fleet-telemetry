import { useVehicles } from "../hooks/useVehicles";
import { VehicleRow } from "./VehicleRow";

export function VehicleList() {
  const { data: vehicles, isLoading, isError } = useVehicles();

  if (isLoading) return <p>Loading vehicles…</p>;
  if (isError) return <p className="error">Failed to load vehicles.</p>;
  if (!vehicles?.length) return <p>No vehicles reporting yet.</p>;

  return (
    <div className="panel">
      <h2>Vehicles ({vehicles.length})</h2>
      <table className="vehicle-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Status</th>
            <th>Battery</th>
            <th>Latest Anomaly</th>
            <th>Position</th>
          </tr>
        </thead>
        <tbody>
          {vehicles.map((v) => (
            <VehicleRow key={v.vehicle_id} vehicle={v} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

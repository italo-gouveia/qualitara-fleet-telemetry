import { useAnomalies } from "../hooks/useAnomalies";

const ANOMALY_BADGE: Record<string, string> = {
  critical_battery: "badge-red",
  fault_entered: "badge-red",
  low_battery: "badge-orange",
  speed_anomaly: "badge-orange",
  error_code_reported: "badge-orange",
};

function relativeTime(iso: string): string {
  const diffSec = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diffSec < 60) return `${diffSec}s ago`;
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
  return `${Math.floor(diffSec / 3600)}h ago`;
}

export function AnomaliesPanel() {
  const { data: anomalies, isLoading, isError } = useAnomalies();

  if (isLoading) return <p>Loading anomalies…</p>;
  if (isError) return <p className="error">Failed to load anomalies.</p>;

  return (
    <div className="panel">
      <h2>
        Recent Anomalies
        {anomalies?.length ? (
          <span className="panel-count">{anomalies.length}</span>
        ) : null}
      </h2>
      {!anomalies?.length ? (
        <p className="anomaly-empty">No anomalies detected.</p>
      ) : (
        <table className="anomaly-table">
          <thead>
            <tr>
              <th>Vehicle</th>
              <th>Type</th>
              <th>Detected</th>
            </tr>
          </thead>
          <tbody>
            {anomalies.map((a) => (
              <tr key={a.id}>
                <td className="anomaly-vehicle">{a.vehicle_id}</td>
                <td>
                  <span className={`badge ${ANOMALY_BADGE[a.type] ?? "badge-slate"}`}>
                    {a.type.replace(/_/g, " ")}
                  </span>
                </td>
                <td className="coord">{relativeTime(a.detected_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

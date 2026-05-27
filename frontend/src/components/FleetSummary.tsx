import { useFleetState } from "../hooks/useFleetState";

const STATUS_COLORS: Record<string, string> = {
  idle: "#94a3b8",
  moving: "#3b82f6",
  charging: "#22c55e",
  fault: "#ef4444",
};

export function FleetSummary() {
  const { data, isLoading } = useFleetState();

  if (isLoading || !data) return <div className="fleet-summary">Loading fleet state…</div>;

  return (
    <div className="fleet-summary">
      <h2>Fleet Summary — {data.total} vehicles</h2>
      <div className="status-tiles">
        {(["idle", "moving", "charging", "fault"] as const).map((s) => (
          <div key={s} className="status-tile" style={{ borderColor: STATUS_COLORS[s] }}>
            <span className="tile-count">{data[s]}</span>
            <span className="tile-label">{s}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

import { useZoneCounts } from "../hooks/useZoneCounts";

const HIGH_THRESHOLD = 10;

export function ZoneCountsPanel() {
  const { data: zones, isLoading, isError } = useZoneCounts();

  if (isLoading) return <p>Loading zones…</p>;
  if (isError) return <p className="error">Failed to load zone counts.</p>;
  if (!zones) return null;

  const sorted = Object.entries(zones).sort(([, a], [, b]) => b - a);

  return (
    <div className="panel">
      <h2>Zone Counts</h2>
      <table className="zone-table">
        <thead>
          <tr>
            <th>Zone</th>
            <th>Entries</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map(([zone, count]) => (
            <tr key={zone} className={count > HIGH_THRESHOLD ? "zone-high" : ""}>
              <td>{zone.replace(/_/g, " ")}</td>
              <td>{count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

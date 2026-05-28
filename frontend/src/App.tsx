import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { FleetSummary } from "./components/FleetSummary";
import { VehicleList } from "./components/VehicleList";
import { ZoneCountsPanel } from "./components/ZoneCountsPanel";
import { AnomaliesPanel } from "./components/AnomaliesPanel";
import "./App.css";

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="app">
        <header className="app-header">
          <h1>Fleet Telemetry Monitor</h1>
          <span className="live-badge">● LIVE</span>
        </header>
        <main className="dashboard">
          <FleetSummary />
          <div className="panels">
            <VehicleList />
            <ZoneCountsPanel />
          </div>
          <AnomaliesPanel />
        </main>
      </div>
    </QueryClientProvider>
  );
}
